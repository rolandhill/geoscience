# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Geoscience - TileServer
                                 A QGIS plugin
 Serves the live QGIS project as XYZ tiles over HTTP on localhost, so that an
 external application can display it as an ordinary XYZ tile source:

     http://127.0.0.1:<port>/{z}/{x}/{y}.png

 Everything runs on the GUI thread. QTcpServer accepts connections
 asynchronously, and QgsMapRendererParallelJob renders asynchronously
 (start() returns immediately, finished() arrives later), so no threads or
 locks are needed and the QGIS UI is never blocked.
 ***************************************************************************/
"""

import json
import re
from urllib.parse import parse_qs

from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice, QObject, QSize, Qt
from qgis.PyQt.QtGui import QColor, QImage
from qgis.PyQt.QtNetwork import QAbstractSocket, QHostAddress, QTcpServer

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsMapRendererCache,
    QgsMapRendererParallelJob,
    QgsMapSettings,
    QgsMessageLog,
    QgsProject,
    QgsTileMatrix,
    QgsTileXYZ,
)

DEFAULT_PORT = 8089
TILE_SIZE = 256
MAX_ZOOM = 24

# QgsMapRendererParallelJob already saturates the thread pool for a single tile, so
# concurrent jobs contend rather than help. Clients routinely open ~6 connections, so
# queue them and keep only a couple of renders in flight.
MAX_IN_FLIGHT = 2

# Rendered (not clipped) margin around each tile, so symbols straddling a tile edge are
# not cut in half. QgsMapSettings.setExtentBuffer() takes map units, so this is scaled
# per zoom level at request time.
EXTENT_BUFFER_PIXELS = 64

MAX_REQUEST_BYTES = 16384

# /{z}/{x}/{y}.png
_TILE_RE = re.compile(r"^/(\d{1,2})/(\d{1,9})/(\d{1,9})\.png$")

_REASONS = {
    200: "OK",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    431: "Request Header Fields Too Large",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


def log(message, level=Qgis.MessageLevel.Info):
    QgsMessageLog.logMessage(message, "Geoscience", level)


class TileServer(QObject):
    """Serves the live project as XYZ tiles on 127.0.0.1."""

    def __init__(self, layersProvider, parent=None):
        """
        Args:
            layersProvider: callable returning the layers to render, topmost first.
                The plugin passes the map canvas layers so that tiles match what the
                user sees. Injected rather than taking iface directly so the server can
                be driven headlessly by tests.
        """
        super().__init__(parent)
        self._layersProvider = layersProvider
        self._server = None
        self._port = 0
        self._revision = 0
        # Shared between jobs; QgsMapRendererCache is the one documented thread-safe
        # piece here, and setCache() does not take ownership, so hold a reference.
        self._cache = QgsMapRendererCache()
        self._buffers = {}   # socket -> bytearray of the request bytes so far
        self._queue = []     # (socket, z, x, y, layerNames) awaiting a free render slot
        self._jobs = {}      # in-flight QgsMapRendererParallelJob -> socket
        self._draining = False

    # ------------------------------------------------------------------ lifecycle

    def isRunning(self):
        return self._server is not None and self._server.isListening()

    def port(self):
        return self._port

    def urlTemplate(self):
        return "http://127.0.0.1:{}/{{z}}/{{x}}/{{y}}.png".format(self._port)

    def start(self, port=DEFAULT_PORT):
        """Start listening. Raises RuntimeError if the port cannot be bound.

        Binds the loopback address only: this serves the project with no
        authentication and must never be reachable off the machine.
        """
        if self.isRunning():
            return

        server = QTcpServer(self)
        if not server.listen(QHostAddress(QHostAddress.SpecialAddress.LocalHost), port):
            reason = server.errorString()
            server.deleteLater()
            # Deliberately do not fall back to another port: the application is
            # configured with a fixed URL and would silently stop finding us.
            raise RuntimeError("Could not listen on 127.0.0.1:{} - {}".format(port, reason))

        server.newConnection.connect(self._onNewConnection)
        self._server = server
        self._port = server.serverPort()
        log("Tile server listening on {}".format(self.urlTemplate()))

    def stop(self):
        """Stop listening, drop pending work and cancel in-flight renders."""
        if self._server is not None:
            self._server.close()
            self._server.deleteLater()
            self._server = None

        self._queue.clear()

        # Disconnect before cancelling: cancel() blocks until the job is done and
        # finished() has already been emitted by the time it returns, so leaving the
        # slot connected would call back into a server we are tearing down.
        for job in list(self._jobs):
            try:
                job.finished.disconnect()
            except (TypeError, RuntimeError):
                pass
            job.cancel()
        self._jobs.clear()

        for socket in list(self._buffers):
            self._closeSocket(socket)
        self._buffers.clear()
        self._port = 0
        log("Tile server stopped")

    # ------------------------------------------------------------------ revision

    def revision(self):
        """A counter the client polls to learn that the rendered map has changed.

        Bumping is left to the caller, which owns the QGIS signals: this class takes its
        layers through a callable so it can be driven headlessly, and reaching for iface
        here would undo that.
        """
        return self._revision

    def bump(self):
        """Record that something affecting the rendered map has changed."""
        self._revision += 1
        # QgsMapRendererCache drops a layer's image on repaintRequested but not on
        # styleChanged, so a symbology change that does not also repaint would go on
        # serving the image rendered before it.
        self._cache.clear()

    # ------------------------------------------------------------------ connections

    def _onNewConnection(self):
        while self._server is not None and self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                break
            self._buffers[socket] = bytearray()
            socket.readyRead.connect(lambda s=socket: self._onReadyRead(s))
            socket.disconnected.connect(lambda s=socket: self._onDisconnected(s))

    def _onReadyRead(self, socket):
        buf = self._buffers.get(socket)
        if buf is None:
            # Header already consumed; we are GET-only so any trailing body is ignored.
            return

        buf += bytes(socket.readAll())

        if len(buf) > MAX_REQUEST_BYTES:
            self._buffers.pop(socket, None)
            self._sendError(socket, 431)
            return

        # readyRead can deliver a partial request; wait for the end of the headers.
        end = buf.find(b"\r\n\r\n")
        if end < 0:
            return

        self._buffers.pop(socket, None)
        self._dispatch(socket, bytes(buf[:end]))

    def _onDisconnected(self, socket):
        self._buffers.pop(socket, None)
        socket.deleteLater()

    def _isLive(self, socket):
        try:
            return (
                socket is not None
                and socket.state() == QAbstractSocket.SocketState.ConnectedState
            )
        except RuntimeError:
            # Underlying C++ socket already deleted.
            return False

    def _closeSocket(self, socket):
        try:
            socket.disconnectFromHost()
        except RuntimeError:
            pass

    # ------------------------------------------------------------------ routing

    def _dispatch(self, socket, header):
        line = header.split(b"\r\n", 1)[0].decode("latin-1", "replace")
        parts = line.split(" ")
        if len(parts) != 3:
            self._sendError(socket, 400)
            return

        method, target = parts[0], parts[1]
        if method != "GET":
            self._sendError(socket, 405)
            return

        path, _, query = target.partition("?")

        if path == "/status":
            self._sendStatus(socket)
            return

        match = _TILE_RE.match(path)
        if match is None:
            self._sendError(socket, 404)
            return

        z, x, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if z > MAX_ZOOM:
            self._sendError(socket, 400)
            return
        limit = 1 << z
        if x >= limit or y >= limit:
            self._sendError(socket, 400)
            return

        self._queue.append((socket, z, x, y, self._parseLayers(query)))
        self._drain()

    def _parseLayers(self, query):
        if not query:
            return []
        values = parse_qs(query).get("layers", [])
        if not values:
            return []
        return [name for name in values[0].split(",") if name]

    # ------------------------------------------------------------------ rendering

    def _drain(self):
        # finished() can be emitted synchronously from start() when the settings are
        # invalid, which re-enters here through _onJobFinished. Guard so the outer loop
        # keeps ownership rather than recursing once per queued tile.
        if self._draining:
            return
        self._draining = True
        try:
            while self._queue and len(self._jobs) < MAX_IN_FLIGHT:
                socket, z, x, y, names = self._queue.pop(0)
                if not self._isLive(socket):
                    continue
                self._render(socket, z, x, y, names)
        finally:
            self._draining = False

    def _render(self, socket, z, x, y, names):
        try:
            settings = self._mapSettings(z, x, y, names)
        except Exception as e:
            log("Tile {}/{}/{} failed: {}".format(z, x, y, e), Qgis.MessageLevel.Warning)
            self._sendError(socket, 500)
            return

        job = QgsMapRendererParallelJob(settings)
        job.setCache(self._cache)
        self._jobs[job] = socket
        # Connect before start(): if the settings are invalid, QgsMapRendererJob::start()
        # emits finished() synchronously rather than after a round of the event loop.
        job.finished.connect(lambda j=job: self._onJobFinished(j))
        job.start()

    def _mapSettings(self, z, x, y, names):
        matrix = QgsTileMatrix.fromWebMercator(z)
        # QgsTileMatrix::tileExtent() measures rows down from yMaximum, i.e. row 0 is the
        # top -- the XYZ/OSM convention. No y flip. (TMS would need y = 2**z - 1 - y.)
        extent = matrix.tileExtent(QgsTileXYZ(x, y, z))

        settings = QgsMapSettings()
        settings.setExtent(extent)
        settings.setOutputSize(QSize(TILE_SIZE, TILE_SIZE))
        settings.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
        settings.setLayers(self._resolveLayers(names))
        settings.setBackgroundColor(QColor(Qt.GlobalColor.transparent))
        settings.setOutputImageFormat(QImage.Format.Format_ARGB32_Premultiplied)
        settings.setExtentBuffer(EXTENT_BUFFER_PIXELS * extent.width() / TILE_SIZE)
        settings.setFlag(Qgis.MapSettingsFlag.RenderMapTile, True)
        settings.setFlag(Qgis.MapSettingsFlag.Antialiasing, True)
        settings.setFlag(Qgis.MapSettingsFlag.DrawLabeling, True)
        # Never set RenderBlocking here. It loads remote sources on the calling thread and
        # qgis.h warns it must never be used from a GUI application. The cost is that
        # remote layers in the project may render incompletely.
        return settings

    def _resolveLayers(self, names):
        # Resolved per request: QgsMapSettings stores layers as weak pointers, and the
        # canvas contents change under us.
        if not names:
            return list(self._layersProvider())

        project = QgsProject.instance()
        layers = []
        for name in names:
            # mapLayersByName returns a list; layer names are not unique.
            found = project.mapLayersByName(name)
            if found:
                layers.append(found[0])
        return layers

    def _onJobFinished(self, job):
        socket = self._jobs.pop(job, None)
        try:
            if not self._isLive(socket):
                return
            payload = self._encodePng(job.renderedImage())
            if payload is None:
                self._sendError(socket, 500)
            else:
                self._send(socket, 200, "image/png", payload)
        finally:
            job.deleteLater()
            self._drain()

    def _encodePng(self, image):
        if image is None or image.isNull():
            return None
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        ok = image.save(buffer, "PNG")
        buffer.close()
        return bytes(data) if ok else None

    # ------------------------------------------------------------------ responses

    def _send(self, socket, status, contentType, payload):
        head = (
            "HTTP/1.1 {} {}\r\n"
            "Content-Type: {}\r\n"
            "Content-Length: {}\r\n"
            # The live project changes under the client, so tiles must not be cached.
            "Cache-Control: no-store\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(status, _REASONS.get(status, "OK"), contentType, len(payload))
        try:
            socket.write(head.encode("latin-1"))
            socket.write(payload)
            socket.disconnectFromHost()
        except RuntimeError:
            pass

    def _sendError(self, socket, status):
        if not self._isLive(socket):
            return
        body = _REASONS.get(status, "Error").encode("latin-1")
        self._send(socket, status, "text/plain; charset=utf-8", body)

    def _sendStatus(self, socket):
        project = QgsProject.instance()
        try:
            layers = list(self._layersProvider())
        except Exception:
            layers = []
        body = json.dumps(
            {
                "project": project.fileName() or project.title(),
                "layers": [layer.name() for layer in layers],
                "qgis": Qgis.QGIS_VERSION,
                "url": self.urlTemplate(),
                # Polled by the client to decide when to re-request its tiles.
                "revision": self._revision,
            }
        ).encode("utf-8")
        self._send(socket, 200, "application/json", body)
