# -*- coding: utf-8 -*-
"""
Created on Tue Jun 05 07:42:15 2018

@author: HillR
"""
# List of original X values
# List of original Y values
# List of required X values
# Return list of required Y splined values

def spline(x, y, xs):
    numOrg = len(x)
    numReq = len(xs)
     
#    int count
#    int count2
    h = [float] * numOrg
    d = [float] * numOrg
    d2y = [float] * numOrg
    p = [float] * numOrg
    q = [float] * numOrg
    a = [float] * numOrg
    b = [float] * numOrg
    c = [float] * numOrg
    s = [float] * numOrg
#    float dv
#    float diff
    ys = [float] * numReq
    
    #Intervals and slopes
    for count in range(1, numOrg):
        h[count-1] = x[count]-x[count-1]
        d[count-1] = (y[count]-y[count-1])/h[count-1]
    d[numOrg-1] = d[numOrg-2]
    
    #Slope changes
    for count in range(1, numOrg):
        d2y[count] = d[count] - d[count-1]
    
    """
        SOLVE EQUATIONS FOR s BY double SCAN PROCEDURE. ASSUME
        s(i+1) = p(i) s(i) + q(i), SCAN DOWN FOR p's AND q's, THEN
        SCAN UP FOR s VALUES.
    
        s(n) IS ZERO BY DEFINITION
    """
    
    p[numOrg-2] = 0.0
    q[numOrg-2] = 0.0
    
    """
        RECURSION RELATIONS FOR P's AND Q's. OBTAINED BY SUBSTITUTING
        S(i+1) = P(i) S(i) + Q(i) INTO
    
        h(i-1) S(i-1) + 2 (h(i-1) + h(i)) S(i) + h(i) S(i+1)
    
            = 6((y(i+1)-y(i))/h(i) - (y(i)-y(i-1))/h(i-1))
    
        TO GIVE A LINEAR EXPRESSION FOR S(i) IN TERMS OF S(i-1), AND
        HENCE VALUES FOR P(i-1) AND Q(i-1) IN S(i)=P(i-1) S(i-1)+Q(i-1).
    """
    
    for count in range(numOrg-2, 0, -1):
        dv = 2*(h[count-1]+h[count])+p[count]*h[count]
        p[count-1] = -h[count-1]/dv
        q[count-1] = (6*d2y[count]-q[count]*h[count])/dv
    
    #s[0] is zero by definition
    s[0]=0.0
    
    #Now find other s values
    for count in range(1, numOrg):
        s[count] = p[count-1]*s[count-1]+q[count-1]
    
    #	DERIVE CUBIC POLYNOMIAL CO-EFFICIENTS FROM S VALUES
    for count in range(0, numOrg-1):
        a[count] = (s[count+1]-s[count])/(6*h[count])
        b[count] = s[count]*0.5
        c[count] = (y[count+1]-y[count])/h[count]-h[count]*(a[count]*h[count]+b[count])
    
    # Calculate y values for supplied x
    for count in range(0, numReq):
        for count2 in range(numOrg-1, -1, -1):
            if(xs[count]>=x[count2]):
                break
    
        diff=xs[count]-x[count2]
#        logFile.write("Count/2: %d %d\n" % (count, count2))
#        logFile.flush()
        if diff == 0.0:
            ys[count] = y[count2]
        else:
            ys[count]=y[count2]+diff*(c[count2]+diff*(b[count2]+diff*a[count2]))
    
    return ys

