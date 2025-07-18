import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter



# Coefficients

D = 2

mu = 0.1
k = 0.2
g = 10

# Convection force parameter
beta = 2


#------------------------------------------------------------------------------
# Grid Setup

Lx = 1
Nx = 25
dx = Lx/Nx

x_data = np.linspace( -Lx/2 , Lx/2, Nx+1 )

Ly = 1
Ny = 25
dy = Ly/Ny

y_data = np.linspace( -Ly/2 , Ly/2 , Ny+1 )

X,Y = np.meshgrid( x_data, y_data, indexing='ij' )


dt = 5e-3


# -----------------------------------------------------------------------------
# Methods


def ThomasTriDiag( a, b, c, d ):
    n = len(d)
    cc = [ c[0] / b[0] ]
    dd = [ d[0] / b[0] ]
    for i in range(1, n-1):
        base = b[i] - a[i]*cc[i-1]
        cc.append(  c[i] / base  )
        dd.append(  ( d[i] - a[i] * dd[i-1] ) / base  )
    
    base = b[n-1] - a[n-1] * cc[n-2]
    dd.append(  ( d[n-1] - a[n-1] * dd[n-2] ) / base  )
    
    x = [0]*(n-1) + [ dd[n-1] ]
    for i in range(n-2,-1,-1):
        x[i] = dd[i] - cc[i] * x[i+1]
    
    return x
    

def partial_x(f):
    out = np.zeros_like(f)
    out[1:-1, 1:-1] = ( f[2:, 1:-1] - f[:-2, 1:-1] )/(2*dx)
    return out

def partial_y(f):
    out = np.zeros_like(f)
    out[1:-1, 1:-1] = ( f[1:-1, 2:] - f[1:-1, :-2] )/(2*dy)
    return out

def partial_2_x(f):
    out = np.zeros_like(f)
    out[1:-1, 1:-1] = ( f[2:, 1:-1] - 2*f[1:-1, 1:-1] + f[:-2, 1:-1] )/dx**2
    return out

def partial_2_y(f):
    out = np.zeros_like(f)
    out[1:-1, 1:-1] = ( f[1:-1, 2:] - 2*f[1:-1, 1:-1] + f[1:-1, :-2] )/dy**2
    return out

def Div(u, v):
    return partial_x(u) + partial_y(v)

def Laplacian(f):
    return partial_2_x(f) + partial_2_y(f)



# -----------------------------------------------------------------------------
# Main Methods
  

first_x = np.array( [1] + [0]*(Nx-2) )
first_y = np.array( [1] + [0]*(Ny-2) )

last_x = np.array( [0]*(Nx-2) + [1] )
last_y = np.array( [0]*(Ny-2) + [1] )  


# Generalised Flow methods with Dirichlet Boundary Conditions

def Flow_Dirichlet( u, v, D, F, S, k ):
    F1 = np.zeros_like(F)
    for i in range(1,Nx):
        a = -0.5/dy * D * v[i,1:-1] - k/dy**2
        c = 0.5/dy * D * v[i,1:-1] - k/dy**2
        b = np.ones_like(a) * ( 2 * D / dt + 2*k/dy**2 )
        d = (
                - a * first_y * F[i,0] - c * last_y * F[i,-1]
                + 2 * D / dt * F[i,1:-1]
                - D * u[i, 1:-1] * partial_x(F)[i, 1:-1]
                + k * partial_2_x(F)[i, 1:-1]
                + S[i, 1:-1]
            )
        scratch = ThomasTriDiag(a, b, c, d)
        F1[i, 1:-1] = scratch
        
    F1[0] = F[0]
    F1[-1] = F[-1]
    F1[:,0] = F[:,0]
    F1[:,-1] = F[:, 0]
    
    F2 = np.zeros_like(F)
    for j in range(1,Ny):
        a = -0.5/dx * D * u[1:-1, j] - k/dx**2
        c = 0.5/dx * D * u[1:-1, j] - k/dx**2
        b = np.ones_like(a) * ( 2 * D / dt + 2*k/dx**2 )
        d = (
                - a * first_x * F1[0,j] - c * last_x * F1[-1,j]
                + 2 * D / dt * F1[1:-1, j]
                - D * v[1:-1, j] * partial_y(F1)[1:-1, j]
                + k * partial_2_y(F1)[1:-1, j]
                + S[1:-1, j]
            )
        scratch = ThomasTriDiag(a, b, c, d)
        F2[1:-1, j] = scratch
    
    F2[0] = F1[0]
    F2[-1] = F1[-1]
    F2[:,0] = F1[:,0]
    F2[:,-1] = F1[:, 0]
    
    return F2



# Generalised Flow methods with Mixed (Robyn) Boundary Conditions
# -- Dirichlet in the x-direction, Neumann in the y-direction

def Flow_Mixed( u, v, D, F, S, k ):
    F1 = np.zeros_like(F)
    for i in range(1,Nx):
        a = -0.5/dy * D * v[i,1:-1] - k/dy**2
        c = 0.5/dy * D * v[i,1:-1] - k/dy**2
        b = ( 2 * D / dt + 2*k/dy**2 ) + a * first_y + c * last_y
        d = (
                2 * D / dt * F[i,1:-1]
                - D * u[i, 1:-1] * partial_x(F)[i, 1:-1]
                + k * partial_2_x(F)[i, 1:-1]
                + S[i, 1:-1]
            )
        scratch = ThomasTriDiag(a, b, c, d)
        F1[i, 1:-1] = scratch
        
    F1[0] = F[0]
    F1[-1] = F[-1]
    F1[:,0] = F1[:,1]
    F1[:,-1] = F1[:,-2]
    
    F2 = np.zeros_like(F)
    for j in range(1,Ny):
        a = -0.5/dx * D * u[1:-1, j] - k/dx**2
        c = 0.5/dx * D * u[1:-1, j] - k/dx**2
        b = ( 2 * D / dt + 2*k/dx**2 ) * np.ones_like(a)
        d = (
                - a * first_x * F1[0,j] - c * last_x * F1[-1,j]
                + 2 * D / dt * F1[1:-1, j]
                - D * v[1:-1, j] * partial_y(F1)[1:-1, j]
                + k * partial_2_y(F1)[1:-1, j]
                + S[1:-1, j]
            )
        scratch = ThomasTriDiag(a, b, c, d)
        F2[1:-1, j] = scratch
    
    F2[0] = F1[0]
    F2[-1] = F1[-1]
    F2[:,0] = F2[:,1]
    F2[:,-1] = F2[:,-2]
    
    return F2



# -----------------------------------------------------------------------------
# Main Stepper Method


def stepper2D_NoProj( u, v, D, Q, fx, fy, S, mu, k ):
    u1 = Flow_Dirichlet( u, v, D, u, fx, mu )
    v1 = Flow_Dirichlet( u, v, D, v, fy, mu )
    Q1 = Flow_Mixed(u, v, D, Q, S, k)
    return u1, v1, Q1



# -----------------------------------------------------------------------------
# Poisson Equation Iterative Solver


# -- Sub-optimal method which involves seeking steady state solutions of a
# -- 'sourced' heat/diffusion equation using ADI methods

firstlast_x = np.array( [1] + [0]*(Nx-3) + [1] )
firstlast_y = np.array( [1] + [0]*(Ny-3) + [1] )


def PoissonSolver_step( w, F, h ):
    w1 = np.zeros_like(w)
    a = c = -h/dy**2 * np.ones( Ny-1 )
    b = ( 1 + 2*h/dy**2 ) * np.ones( Ny-1 ) + a * firstlast_y
    for i in range(1,Nx):
        d = w[i, 1:-1] - h * F[i, 1:-1] + h * partial_2_x(w)[i, 1:-1]
        scratch = ThomasTriDiag(a, b, c, d)
        w1[i, 1:-1] = scratch
    
    w1[0] = w1[1]
    w1[-1] = w1[-2]
    w1[:,0] = w1[:,1]
    w1[:,-1] = w1[:,-2]

    w2 = np.zeros_like(w1)
    a = c = -h/dx**2 * np.ones( Nx-1 )
    b = ( 1 + 2*h/dx**2 ) * np.ones( Nx-1 ) + a * firstlast_x
    for j in range(1,Ny):
        d = w1[1:-1, j] - h * F[1:-1, j] + h * partial_2_y(w1)[1:-1, j]
        scratch = ThomasTriDiag(a, b, c, d)
        w2[1:-1, j] = scratch
    
    w2[0] = w2[1]
    w2[-1] = w2[-2]
    w2[:,0] = w2[:,1]
    w2[:,-1] = w2[:,-2]
    
    return w2


def PoissonSolver( w, F, h, Nstep ):
    w1 = w
    for step in range(Nstep):
        w1 = PoissonSolver_step(w1, F, h)
    
    return w1
    


# -----------------------------------------------------------------------------
# Chorin Projection


def rect_smooth(x, q, L):
    if 0 <= x <= q:
        return 1/q**4 * x**2 * ( x - 2*q )**2
    elif q < x < L-q:
        return 1
    elif L-q <= x <= L:
        return 1/q**4 * ( L-x )**2 * ( L-x - 2*q )**2
    else:
        return 0

def env_fun(x, y):
    return rect_smooth( x+Lx/2, 0.2*Lx, Lx) * rect_smooth( y+Ly/2, 0.2*Ly, Ly)

env_arr = np.array( [ [ env_fun(x, y) for y in y_data ] for x in x_data ] )


def Chorin( u, v, h ):
    F = Div(u, v)
    p0 = np.zeros_like(u)
    p1 = PoissonSolver( p0, F, h, 25 )
    u1 = u - env_arr * partial_x(p1)
    v1 = v - env_arr * partial_y(p1)
    
    return u1, v1




# Complete Stepper Method

h = 1e-3

def stepper2D_Full( u, v, D, Q, fx, fy, S, mu, k ):
    u0, v0, Q1 = stepper2D_NoProj(u, v, D, Q, fx, fy, S, mu, k)
    u1, v1 = Chorin( u0, v0, h )
    return u1, v1, Q1


# -----------------------------------------------------------------------------
# Array Shortening

# -- When choosing large values of Nx and Ny, one constructs smaller
# -- u,v arrays (flow velocity components) for the purposes of creating
# -- better quiver plots

Nx_ticks = 20
Ny_ticks = 20

resx = int( np.floor( Nx/Nx_ticks ) )
resy = int( np.floor( Ny/Ny_ticks ) )

x_ind = np.arange( 0, Nx+1, step=resx )
y_ind = np.arange( 0, Ny+1, step=resy )

x_short = np.array( [ x_data[i] for i in x_ind ] )
y_short = np.array( [ y_data[i] for i in y_ind ] )

Xs, Ys = np.meshgrid( x_short, y_short, indexing='ij' )

def array_shorten( arr ):
    return np.array( [ [ arr[i,j] for j in y_ind ] for i in x_ind ] )



# -----------------------------------------------------------------------------
# Initial State



def env_x( x ):
    return rect_smooth( x+Lx/2, 0.1*Lx, Lx/2 )

def env_y( y ):
    return rect_smooth( y+Ly/2, 0.1*Ly, Ly/2 )

wrap1 = np.array( [ [ env_x(x) * env_y(y) for y in y_data ] for x in x_data ] )




u0 = v0 = np.zeros_like(X)

Q0 = D * ( 0.5 - X/Lx )


# Flow Sources
fx, fy = np.zeros_like(X) , - D * g * (  1 + beta * partial_y( Q0 )  )


# Heat Source
S = 2 * D * wrap1


# Set Initial Values
u, v, Q = u0, v0, Q0



# Number of time steps
max_step = 200



# -----------------------------------------------------------------------------
# PLotting


plot_title = (  'Flow Velocity Plot: rho='+ str(D)
              + ', mu=' + str(mu) 
              + ', k=' + str(k)
              + ', t_max=' + str(max_step * dt)
              )


fig = plt.figure( figsize=[10,8], dpi=80 )
fig.suptitle( plot_title )

ax = fig.add_subplot()

ax.set_xlabel( 'x' )
ax.set_ylabel( 'y' )

shortzeros = np.zeros_like(Xs)

h_plot = ax.pcolormesh( X, Y, np.zeros_like(X), vmin=0, vmax=2 )

fig.colorbar( h_plot, ax=ax )

q_plot = ax.quiver( Xs, Ys, shortzeros, shortzeros , pivot='middle')


plt.show()



# -----------------------------------------------------------------------------
# Animation Setup



MD = dict( title='', artist='' )
writer = PillowWriter( fps=10, metadata=MD )



with writer.saving( fig, 'Flow Example 1.gif', max_step ):
    for step in range(max_step):
        q_plot.remove()
        h_plot.remove()
        
        # u_short = array_shorten(u)
        # v_short = array_shorten(v)
        
        # speed = np.sqrt(  u**2 + v**2 )
        
        h_plot = ax.pcolormesh( X, Y, Q, vmin=0, vmax=2 )
        q_plot = ax.quiver( Xs, Ys, u, v, pivot='middle' )

        fy = - D * g * (  1 + beta * partial_y( Q )  )
        
        u,v,Q = stepper2D_Full(u, v, D, Q, fx, fy, S, mu, k)
        
        writer.grab_frame()








# for step in range(10):
#     fy = - D * g * (  1 + beta * partial_y( Q )  )
    
#     u,v,Q = stepper2D_Full(u, v, D, Q, fx, fy, S, mu, k)


# q_plot.remove()
# h_plot.remove()

# h_plot = ax.pcolormesh( X, Y, Q, vmin=0, vmax=2 )
# q_plot = ax.quiver( Xs, Ys, u, v, pivot='middle' )
    
    