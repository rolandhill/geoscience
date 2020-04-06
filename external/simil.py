# -*- coding: utf-8 -*-
"""
Find similarity transformation parameters given a set of control points

A partial implementation of the algorithm described by Zeng et al.,
2018[1]_.  

Given a set of 3-D control points, the algorithm solves an optimization
problem to find the parameters of the similarity transformation
that minimizes the error of the solution, using the mathematical
concepts of dual numbers and quaternions.  

Source and target control points coordinates are passed as arguments to
the `process` function, which returns the values for M (multiplier
factor), R (rotation matrix), and T (translation vector).  

Once the parameters have been solved, transform coordinates with the
following formula:
    
    ``XYZ_t = M * R * XYZ_s + T``
    
Where:
- ``XYZ_t`` are the coordinates of the target points.
- ``M`` is the multiplier factor (`lambda_i`).
- ``R`` is the rotation matrix (`r_matrix`).
- ``XYZ_s`` are the coordinates of the source points.
- ``T`` is the translation vector (`t_vector`).

Per point weights can be used.  
The solution can be forced to mirror and/or to fixed scale.  


Notes
-----

Requires `numpy`.

References
----------

.. [1] Huaien Zeng, Xing Fang, Guobin Chang and Ronghua Yang (2018)
A dual quaternion algorithm of the Helmert transformation problem.
Earth, Planets and Space (2018) 70:26.
(https://doi.org/10.1186/s40623-018-0792-x)

Examples
--------

Common usage.

>>> import numpy as np
>>> np.set_printoptions(precision=3, suppress=True)
>>> import simil
>>> source_points = [[0, 0, 0],
...                  [0, 2, 2],
...                  [2, 3, 1],
...                  [3, 1, 2],
...                  [1, 1, 3]]
>>> target_points = [[3.0, 7.0, 5.0],
...                  [6.0, 7.0, 2.0],
...                  [4.5, 4.0, 0.5],
...                  [6.0, 2.5, 3.5],
...                  [7.5, 5.5, 3.5]]
>>> m, r, t = simil.process(source_points, target_points)
>>> m
1.5000000000000016
>>> r
array([[-0.,  0.,  1.],
       [-1., -0., -0.],
       [ 0., -1.,  0.]])
>>> t
array([[3.],
       [7.],
       [5.]])

To transform, we need coordinates (instead of points) in the rows,
so transpose:
    
>>> source_coords = np.array(source_points).T
>>> target_coords = m * r @ source_coords + t
>>> print(target_coords.T)
[[3.  7.  5. ]
 [6.  7.  2. ]
 [4.5 4.  0.5]
 [6.  2.5 3.5]
 [7.5 5.5 3.5]]

To force a fixed scale of 1.25:

>>> m, r, t = simil.process(source_points,
...                         target_points, 
...                         scale=False, 
...                         lambda_0=1.25)
>>> m
1.25
>>> print((m * r @ source_coords + t).T)
[[3.4  6.7  4.65]
 [5.9  6.7  2.15]
 [4.65 4.2  0.9 ]
 [5.9  2.95 3.4 ]
 [7.15 5.45 3.4 ]]

To force mirroring the source points: 

>>> m, r, t = simil.process(source_points, target_points, lambda_0=-1)
>>> print((m * r @ source_coords + t).T)
[[4.385 6.758 3.124]
 [5.329 4.987 3.951]
 [4.739 3.984 2.475]
 [6.097 4.987 1.648]
 [6.451 5.283 3.301]]

Per point weights can be passed as a list:

>>> alpha_0 = [100, 20, 2, 20, 50]
>>> m, r, t = simil.process(source_points,
...                         target_points,
...                         alpha_0=alpha_0,
...                         scale=False,
...                         lambda_0=1)
>>> print((m * r @ source_coords + t).T)
[[3.604 6.703 4.698]
 [5.604 6.703 2.698]
 [4.604 4.703 1.698]
 [5.604 3.703 3.698]
 [6.604 5.703 3.698]]
"""

import numpy as np

# =================
# Private functions
# =================

def _get_scalar(alpha_0, q_coords=None):
    if q_coords is None:
        scalar = np.einsum('i->', alpha_0)
    else:
        scalar = np.einsum('i,i->', alpha_0, (q_coords * q_coords).sum(0))
    return scalar

def _get_q_matrix(quaternions):
    q_matrix = [[[q[3], -q[2], q[1], q[0]],
                 [q[2], q[3] , -q[0], q[1]],
                 [-q[1], q[0], q[3], q[2]],
                 [-q[0], -q[1], -q[2], q[3]]] for q in quaternions]
    return np.array(q_matrix)

def _get_w_matrix(quaternions):
    w_matrix = [[[q[3], q[2], -q[1], q[0]],
                 [-q[2], q[3] , q[0], q[1]],
                 [q[1], -q[0], q[3], q[2]],
                 [-q[0], -q[1], -q[2], q[3]]] for q in quaternions]
    return np.array(w_matrix)

def _get_abc_matrices(alpha_0, m1, m2=None):
    if m2 is None:
        matrix = np.einsum('i,ijk->jk', alpha_0, m1)
    else:
        matrix = np.einsum('i,ijk->jk',
                           alpha_0,
                           np.transpose(m1, (0,2,1)) @ m2)
    return matrix

def _get_blc_matrix(b_matrix, lambda_i, c_matrix):
    blc_matrix = b_matrix - lambda_i*c_matrix
    return blc_matrix

def _get_d_matrix(li, cs, am, blcm):
    d_matrix = 2*li*am + (1/cs)*(blcm.T @ blcm)
    return d_matrix

def _get_r_quat(d_matrix):
    eigvals, eigvects = np.linalg.eig(d_matrix)
    beta_1 = np.argmax(eigvals)
    r_quat = eigvects[:,beta_1]
    return beta_1, r_quat

def _get_lambda_next(am, bs, bm, cs, cm, rq):
    expr_1 = rq.T @ am @ rq
    expr_2 = (1/cs) * (rq.T @ bm.T @ cm @ rq)
    expr_3 = (1/cs) * (rq.T @ cm.T @ cm @ rq)
    lambda_next = (expr_1-expr_2) / (bs-expr_3)
    return lambda_next

def _get_solution(am, bs, bm, cs, cm, scale, li, i):
    blc_matrix = _get_blc_matrix(bm, li, cm)
    d_matrix = _get_d_matrix(li, cs, am, blc_matrix)
    beta_1, r_quat = _get_r_quat(d_matrix)
    if scale is False:
        return blc_matrix, d_matrix, beta_1, r_quat, li, i
    else:
        lambda_next = _get_lambda_next(am, bs, bm, cs, cm, r_quat)
        if abs(li-lambda_next) < 0.000001:
            return blc_matrix, d_matrix, beta_1, r_quat, li, i
        else:
            li, i = lambda_next, i+1
            return _get_solution(am, bs, bm, cs, cm, scale, li, i)

def _get_r_matrix(r_quat):
    r_w_matrix = _get_w_matrix([r_quat])[0]
    r_q_matrix = _get_q_matrix([r_quat])[0]
    r_matrix = (r_w_matrix.T @ r_q_matrix)[:3,:3]
    return r_matrix

def _get_s_quat(c_scalar, blcm, r_quat):
    s_quat = 1/(2*c_scalar) * (blcm @ r_quat)
    return s_quat

def _get_t_vector(r_quat, s_quat):
    r_w_matrix = _get_w_matrix([r_quat])[0]
    t_vector = [2 * (r_w_matrix.T @ s_quat)[:3]]
    return t_vector 
   
# ================
# Process function
# ================
    
def process(source_points,
            target_points,
            alpha_0=None,
            scale=True,
            lambda_0=1.0):
    """
    Find similarity transformation parameters given a set of control points
    
    Parameters
    ----------
    source_points : array_like
        The function will try to cast it to a numpy array with shape:
        ``(n, 3)``, where ``n`` is the number of points.
        Two points is the minimum requeriment (in that case, the solution
        will map well all points that belong in the rect that passes 
        through both control points).
    target_points : array_like
        The function will try to cast it to a numpy array with shape:
        ``(n, 3)``, where ``n`` is the number of points.
        The function will check that there are as many target points
        as source points.
    alpha_0 : array_like, optional
        Per point weights.
        If provided, the function will try to cast to a numpy array with
        shape: ``(n,)``.
    scale : boolean, optional
        Allow to find a multiplier factor different from lambda_0.
        Default is True.
    lambda_0 : float, optional
        Multiplier factor to find the first solution. Default is 1.0.
        If `scale=True`, a recursion is implemented to find a better
        value. If it is negative, forces mirroring. Can't be zero.

    Returns
    -------
    lambda_i : float
        Multiplier factor.
    r_matrix : numpy.ndarray
        Rotation matrix.
    t_vector : numpy.ndarray
        Translation (column) vector.
    """
    
    
    # declarations and checkups

    source_coords = np.array(source_points, dtype=float).T

    if source_coords.ndim != 2:
        err_msg = ('source_points array must have dimension = 2.')
        raise ValueError(err_msg)
        
    if source_coords.shape[0] != 3:
        err_msg = ('There are not three coordinates in source points.')
        raise ValueError(err_msg)        
    
    n = source_coords.shape[1]

    if (n == 1 or (source_coords[None,0] == source_coords).all()):
        err_msg = ('There are not two distinct source points.')
        raise ValueError(err_msg)
        
    target_coords = np.array(target_points, dtype=float).T
    
    if target_coords.ndim != 2:
        err_msg = ('target_points array must have dimension = 2.')
        raise ValueError(err_msg)

    if target_coords.shape[0] != 3:
        err_msg = ('There are not three coordinates in target points.')
        raise ValueError(err_msg)
        
    if target_coords.shape[1] != n:
        err_msg = ('There are not as many target points as source points.')
        raise ValueError(err_msg)

    if alpha_0 is None:
        alpha_0 = np.ones(n)
    else:
        alpha_0 = np.array(alpha_0, dtype=float)

    if alpha_0.ndim != 1:
        err_msg = ('alpha_0 array must have dimension = 1.')
        raise ValueError(err_msg)

    if alpha_0.shape != (n,):
        err_msg = ('There are not as many alpha_0 coefficients as '
                   'control points.')
        raise ValueError(err_msg)

    lambda_0 = float(lambda_0)
    
    if lambda_0 == 0:
        err_msg = ('lambda_0 cannot be zero.')
        raise ValueError(err_msg)


    # processes
    
    source_q_coords = np.concatenate((source_coords,np.zeros((1,n))))
    
    target_q_coords = np.concatenate((target_coords,np.zeros((1,n))))

    b_scalar = _get_scalar(alpha_0, source_q_coords)
    
    c_scalar = np.einsum('i->', alpha_0)
    
    q0_w_matrix = _get_w_matrix(source_q_coords.T)
    
    qt_q_matrix = _get_q_matrix(target_q_coords.T)
    
    a_matrix = _get_abc_matrices(alpha_0, q0_w_matrix, qt_q_matrix)
    
    b_matrix = _get_abc_matrices(alpha_0, qt_q_matrix)
    
    c_matrix = _get_abc_matrices(alpha_0, q0_w_matrix)

    lambda_i, i = lambda_0 , 1

    blc_matrix, d_matrix, beta_1, r_quat, lambda_i, i = _get_solution(a_matrix,
                                                                      b_scalar, 
                                                                      b_matrix, 
                                                                      c_scalar, 
                                                                      c_matrix, 
                                                                      scale, 
                                                                      lambda_i, 
                                                                      i)
    
    r_matrix = _get_r_matrix(r_quat)
    
    s_quat = _get_s_quat(c_scalar, blc_matrix, r_quat)
    
    t_vector = np.array(_get_t_vector(r_quat, s_quat)).reshape(3,1)
    
    return lambda_i, r_matrix, t_vector
