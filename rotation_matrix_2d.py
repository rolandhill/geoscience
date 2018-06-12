'''
This module contains functions to generate 2D rotation matrices.
'''
import math
import numpy as np

def rotation_from_angle(angle):
    '''
    generates a 2x2 rotation matrix from a given angle following
    the definition here:
    https://en.wikipedia.org/wiki/Rotation_matrix.

    :param angle: the angle by which to rotate
    :type angle: float

    :returns: the rotation matrix
    :rtype: a 2x2 :any:`numpy.ndarray`
    '''
    c = math.cos(angle)
    s = math.sin(angle)

    return np.array([[c, -s],[s, c]])
