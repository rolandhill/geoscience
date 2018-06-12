'''
This module contains functions to generate n-D rotation matrices.
'''
import math
import numpy as np

def rotation_from_angle_and_plane(angle, vector1, vector2, abs_tolerance=1e-10):
    '''
    generates an nxn rotation matrix from a given angle and
    a plane spanned by two given vectors of length n:
    https://de.wikipedia.org/wiki/Drehmatrix#Drehmatrizen_des_Raumes_%7F'%22%60UNIQ--postMath-0000003B-QINU%60%22'%7F

    The formula used is

    .. math::

        M = 𝟙 + (\cos\\alpha-1)\cdot(v_1\otimes v_1 + v_2\otimes v_2) - \sin\\alpha\cdot(v_1\otimes v_2 - v_2\otimes v_1)

    with :math:`M` being the returned matrix, :math:`v_1` and :math:`v_2` being the two
    given vectors and :math:`\\alpha` being the given angle. It differs from the formula
    on wikipedia in that it is the transposed matrix to yield results that are consistent
    with the 2D and 3D cases.

    :param angle: the angle by which to rotate
    :type angle: float
    :param vector1: one of the two vectors that span the plane in which to rotate
                    (no normalisation required)
    :type vector1: array like
    :param vector2: the other of the two vectors that span the plane in which to rotate
                    (no normalisation required)
    :type vector2: array like
    :param abs_tolerance: The absolute tolerance to use when checking if vectors have length 0 or are parallel.
    :type abs_tolerance: float

    :returns: the rotation matrix
    :rtype: an nxn :any:`numpy.ndarray`
    '''

    vector1 = np.asarray(vector1, dtype=np.float)
    vector2 = np.asarray(vector2, dtype=np.float)

    vector1_length = np.linalg.norm(vector1)
    if math.isclose(vector1_length, 0., abs_tol=abs_tolerance):
        raise ValueError(
            'Given vector1 must have norm greater than zero within given numerical tolerance: {:.0e}'.format(abs_tolerance))

    vector2_length = np.linalg.norm(vector2)
    if math.isclose(vector2_length, 0., abs_tol=abs_tolerance):
        raise ValueError(
            'Given vector2 must have norm greater than zero within given numerical tolerance: {:.0e}'.format(abs_tolerance))

    vector2 /= vector2_length
    dot_value = np.dot(vector1, vector2)

    if abs(dot_value / vector1_length ) > 1 - abs_tolerance:
        raise ValueError(
            'Given vectors are parallel within the given tolerance: {:.0e}'.format(abs_tolerance))

    if abs(dot_value / vector1_length ) > abs_tolerance:
        vector1 = vector1 - dot_value * vector2
        vector1 /= np.linalg.norm(vector1)
    else:
        vector1 /= vector1_length


    vectors = np.vstack([vector1, vector2]).T
    vector1, vector2 = np.linalg.qr(vectors)[0].T

    V = np.outer(vector1, vector1) + np.outer(vector2, vector2)
    W = np.outer(vector1, vector2) - np.outer(vector2, vector1)

    return np.eye(len(vector1)) + (math.cos(angle) - 1)*V - math.sin(angle)*W





def random_matrix(n):
    '''
    Generate a nxn random matrix.
    The distribution of rotations is uniform on the n-sphere.
    The random matrix is from the O(n) group (not SO(n)) and uses the
    gram-schmidt algorithm to orthogonalize the random matrix,
    see http://www.ams.org/notices/200511/what-is.pdf
    If a rotation from SO(n) is needed, look for:
    "A statistical model for random rotations" doi:10.1016/j.jmva.2005.03.009

    :param n: dimension of space in which the rotation operates
    :type n: int
    :returns: rotation matrix
    :rtype: a nxn :any:`numpy.ndarray`
    '''
    if n < 2:
        raise ValueError('n must be greater than 1 but is ' + str(n) + '.')

    a = np.random.randn(n,n)

    a[0] = a[0]/np.linalg.norm(a[0])

    max_iter = n*(n-1)//2
    base = 0
    mod = base + 1
    for _ in range(0,max_iter):
        a[mod] = a[mod] - a[base]*np.dot(a[mod],a[base])
        a[mod] = a[mod]/np.linalg.norm(a[mod])

        if mod < n-1:
            mod += 1
        else:
            base += 1
            mod = base + 1
    return a
