# AI Agent Instructions for Geoscience plugin for QGIS

## CRITICAL OUTPUT CONSTRAINTS
- **Keep responses short, concise, and action-oriented.**
- **Code Changes:** Prefer minimal, focused edits. Do not rewrite entire files; output only the relevant function or block modification. 
- **Format:** Respond strictly in plain Markdown code blocks. Do not invent raw XML tags or format system tool arguments.

---

## SYSTEM & PROJECT BIG PICTURE
- **Application:** Geoscience is a Python plugin for QGIS. Older versions work on QGIS 3, but newer features are targeted at QGIS 4.
- **Python:** Using python 3.12, but should be compatible with Python 3.14
- **Security:** QGIS plugins must pass Bandit security analysis when uploaded to the QGIS plugin repository
---

## DEPENDENCIES & COMPILATION CONTEXT
- **Core Dependencies:** Geoscience provides tile rendering services to Spatial Integration. This is not an essential service.
