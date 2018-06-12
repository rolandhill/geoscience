from scipy import interpolate

def f(x):
    x_points = [ 0, 1, 2, 3, 4, 5]
    y_points = [12,14,22,39,58,77]

    tck = interpolate.splrep(x_points, y_points)
    return interpolate.splev(x, tck)

print f(1.25)




def cubic_spline(x, y):
  """
  Parameters
  ----------
  x  : list of floats
  y  : list of floats

  Returns
  -------  
  list of list of floats
  """
  n = len(x) - 1
  h = [x[i+1]-x[i] for i in range(n)]
  al = [3*((y[i+1]-y[i])/h[i] - (y[i]-y[i-1])/h[i-1]) for i in range(1,n)]
  al.insert(0,0)
  
  l = [1] * (n+1)
  u = [0] * (n+1)
  z = [0] * (n+1)
  for i in range(1, n):
    l[i] = 2*(x[i+1]-x[i-1]) - h[i-1]*u[i-1]
    u[i] = h[i]/l[i]
    z[i] = (al[i] - h[i-1]*z[i-1])/l[i]

  b = [0] * (n+1)
  c = [0] * (n+1)
  d = [0] * (n+1)
  for i in range(n-1, -1, -1):    #for i in reversed(range(n)):
    c[i] = z[i] - u[i]*c[i+1]
    b[i] = (y[i+1]-y[i])/h[i] - h[i]*(c[i+1] + 2*c[i])/3
    d[i] = (c[i+1]-c[i])/(3*h[i])
  return [y, b, c, d]
  
if __name__ == '__main__':
  import math  
  import matplotlib.pyplot as plt
  import numpy as np

  # the function to be interpolated
  def f(x):
    return math.e ** x
    
  # input
  interval = 3
  x = [i for i in range(interval + 1)]
  y = [f(i) for i in range(interval + 1)]

  # process
  a = cubic_spline(x, y)

  # prepare data for plotting the splines
  points_per_interval = 5
  xs = []
  ys = []
  for i in range(3):
    xs.append(np.linspace(i, i+1, points_per_interval))
    ys.append([a[0][i] + 
               a[1][i]*(xs[i][k]-i) + 
               a[2][i]*(xs[i][k]-i)**2 + 
               a[3][i]*(xs[i][k]-i)**3   
               for k in range(points_per_interval)])
  
  # prepare data for plotting the given function
  x = np.linspace(0, 3, interval * points_per_interval - (interval - 1))
  y = [f(x[i]) for i in range(len(x))]

  plt.plot(x, y, 'k.-', xs[0], ys[0], 'r.--', xs[1], ys[1], 'g.--', xs[2], ys[2], 'b.--')

  plt.title('Cubic Spline')
  plt.xlabel('x')
  plt.ylabel('e^x')
  plt.show()
  
# cubic spline interpolation
# author : worasait suwannik
# date   : apr 2015

