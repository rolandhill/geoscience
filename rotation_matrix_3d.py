'''
This module contains functions to generate 3D rotation matrices.
'''

import numpy as np
import math

def rotation_around_axis(axis, angle):
    '''
    Generates a 3x3 rotation matrix using the Euler-Rodrigues formula
    following the definition here:
    https://en.wikipedia.org/wiki/Euler%E2%80%93Rodrigues_formula.

    :param axis: the axis around which to rotate as a vector of length 3
                 (no normalisation required)
    :type axis: array like
    :param angle: the angle in radians to rotate
    :type angle: float

    :returns: the rotation matrix
    :rtype: a 3x3 :any:`numpy.ndarray`
    '''
    axis = axis/np.linalg.norm(axis)

    a = math.cos(angle/2.0)
    b, c, d = axis * math.sin(angle/2.0)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d

    return np.array([[aa+bb-cc-dd, 2*(bc-ad), 2*(bd+ac)],
                     [2*(bc+ad), aa+cc-bb-dd, 2*(cd-ab)],
                     [2*(bd-ac), 2*(cd+ab), aa+dd-bb-cc]])


def rotation_around_x(angle):
    '''
    Generates a 3x3 rotation matrix that performs a rotation around
    the x-axis following the definitions here:
    https://en.wikipedia.org/wiki/Rotation_matrix#Basic_rotations

    :param angle: the angle by which to rotate around the x-axis
    :type angle: float

    :returns: the rotation matrix
    :rtype: a 3x3 :any:`numpy.ndarray`
    '''
    c = math.cos(angle)
    s = math.sin(angle)

    return np.array(
        [[1, 0, 0],
         [0, c, -s],
         [0, s, c]])

def rotation_around_y(angle):
    '''
    Generates a 3x3 rotation matrix that performs a rotation around
    the y-axis following the definitions here:
    https://en.wikipedia.org/wiki/Rotation_matrix#Basic_rotations

    :param angle: the angle by which to rotate around the y-axis
    :type angle: float

    :returns: the rotation matrix
    :rtype: a 3x3 :any:`numpy.ndarray`
    '''
    c = math.cos(angle)
    s = math.sin(angle)

    return np.array(
        [[c, 0, s],
         [0, 1, 0],
         [-s, 0, c]])

def rotation_around_z(angle):
    '''
    Generates a 3x3 rotation matrix that performs a rotation around
    the z-axis following the definitions here:
    https://en.wikipedia.org/wiki/Rotation_matrix#Basic_rotations

    :param angle: the angle by which to rotate around the z-axis
    :type angle: float

    :returns: the rotation matrix
    :rtype: a 3x3 :any:`numpy.ndarray`
    '''
    c = math.cos(angle)
    s = math.sin(angle)

    return np.array(
        [[c, -s, 0],
         [s, c, 0],
         [0, 0, 1]])


# Implementation of the different variations of rotation matrices as
# described in https://en.wikipedia.org/wiki/Euler_angles#Rotation_matrix.

def _generate_matrix_XZX(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[ c2                , -c3*s2            ,  s2*s3            ],
         [ c1*s2             ,  c1*c2*c3 - s1*s3 , -c3*s1 - c1*c2*s3 ],
         [ s1*s2             ,  c1*s3 + c2*c3*s1 ,  c1*c3 - c2*s1*s3 ]])

def _generate_matrix_XYX(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[ c2                ,  s2*s3            ,  c3*s2            ],
         [ s1*s2             ,  c1*c3 - c2*s1*s3 , -c1*s3 - c2*c3*s1 ],
         [ -c1*s2            ,  c3*s1 + c1*c2*s3 ,  c1*c2*c3 - s1*s3 ]])

def _generate_matrix_YXY(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c1*c3 - c2*s1*s3 ,  s1*s2            ,  c1*s3 + c2*c3*s1 ],
         [  s2*s3            ,  c2               , -c3*s2            ],
         [  -c3*s1 -c1*c2*s3 ,  c1*s2            ,  c1*c2*c3 - s1*s3 ]])

def _generate_matrix_YZY(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c1*c2*c3 - s1*s3 , -c1*s2            ,  c3*s1 + c1*c2*s3 ],
         [  c3*s2            ,  c2               ,  s2*s3            ],
         [ -c1*s3 - c2*c3*s1 ,  s1*s2            ,  c1*c3 - c2*s1*s3 ]])

def _generate_matrix_ZYZ(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c1*c2*c3 - s1*s3 , -c3*s1 - c1*c2*s3 ,  c1*s2            ],
         [  c1*s3 + c2*c3*s1 ,  c1*c3 - c2*s1*s3 ,  s1*s2            ],
         [  -c3*s2           ,  s2*s3            ,  c2               ]])

def _generate_matrix_ZXZ(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c1*c3 - c2*s1*s3 , -c1*s3 - c2*c3*s1 ,  s1*s2            ],
         [  c3*s1 + c1*c2*s3 ,  c1*c2*c3 - s1*s3 , -c1*s2            ],
         [  s2*s3            ,  c3*s2            ,  c2               ]])

def _generate_matrix_XZY(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c2*c3            , -s2               ,  c2*s3            ],
         [  s1*s3 + c1*c3*s2 ,  c1*c2            ,  c1*s2*s3 - c3*s1 ],
         [  c3*s1*s2 - c1*s3 ,  c2*s1            ,  c1*c3 + s1*s2*s3 ]])

def _generate_matrix_XYZ(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c2*c3            , -c2*s3            ,  s2               ],
         [  c1*s3 + c3*s1*s2 ,  c1*c3 - s1*s2*s3 , -c2*s1            ],
         [  s1*s3 - c1*c3*s2 ,  c3*s1 + c1*s2*s3 ,  c1*c2            ]])

def _generate_matrix_YXZ(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c1*c3 + s1*s2*s3 ,  c3*s1*s2 - c1*s3 ,  c2*s1            ],
         [  c2*s3            ,  c2*c3            , -s2               ],
         [  c1*s2*s3 - c3*s1 ,  c1*c3*s2 + s1*s3 ,  c1*c2            ]])

def _generate_matrix_YZX(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c1*c2            ,  s1*s3 - c1*c3*s2 ,  c3*s1 + c1*s2*s3 ],
         [  s2               ,  c2*c3            ,  -c2*s3           ],
         [ -c2*s1            ,  c1*s3 + c3*s1*s2 ,  c1*c3 - s1*s2*s3 ]])

def _generate_matrix_ZYX(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c1*c2            ,  c1*s2*s3 - c3*s1 ,  s1*s3 + c1*c3*s2 ],
         [  c2*s1            ,  c1*c3 + s1*s2*s3 ,  c3*s1*s2 - c1*s3 ],
         [ -s2               ,  c2*s3            ,  c2*c3            ]])

def _generate_matrix_ZXY(c1, c2, c3, s1, s2, s3):
    return np.asarray(
        [[  c1*c3 - s1*s2*s3 , -c2*s1            ,  c1*s3 + c3*s1*s2 ],
         [  c3*s1 + c1*s2*s3 ,  c1*c2            ,  s1*s3 - c1*c3*s2 ],
         [ -c2*s3            ,  s2               ,  c2*c3            ]])

# End of wikipedia copy paste


def rotation_from_angles(angles, rotation_sequence):
    '''
    Generate a 3x3 rotation matrix using proper Euler angles or
    Tait-Bryan angles as defined here: https://en.wikipedia.org/wiki/Euler_angles#Rotation_matrix.
    The angles given correspond to rotations as given in rotation_sequence, e.g.::

        rotation_from_angles([np.pi/2, 2/3*np.pi, np.pi/3], 'ZYX')

    would create a rotation matrix equal to the product of a rotation around Z by 90° times
    a rotation around Y by 60° times a rotation around X by 30°. For all the details
    please have a look at the linked wikipedia article.


    :param angles: the three angles in radians that define the rotation as a vector
                   of length 3
    :type angles: array like
    :param rotation_sequence: the sequence of rotations that make up the
                              total rotation. Example: `XYZ` yields the rotation
                              matrix :math:`R=XYZ`, i.e. the product of the
                              three matrices :math:`X`, :math:`Y` and :math:`Z`.
    :type rotation_sequence: str
    :returns: the rotation matrix
    :rtype: a 3x3 :any:`numpy.array`
    '''

    c1, c2, c3 = np.cos(angles)
    s1, s2, s3 = np.sin(angles)
    try:
        return globals()['_generate_matrix_'+rotation_sequence](c1, c2, c3, s1, s2, s3)
    except KeyError:
        raise ValueError(
            'Sequence ' + rotation_sequence
            + ' is not valid.')
