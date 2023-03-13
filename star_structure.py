import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline

class Star:

    def __init__(self, rho_eos, p_center, p_surface):

        # Set the density function as the EOS given (rho(p))
        self.rho = rho_eos

        # Set the integration constants: pressure, mass, and density at r=0
        self.p_0 = p_center
        self.m_0 = 0.0
        self.rho_0 = self.rho(self.p_0)

        # Set the boundary value for the termination of the ODE integration: pressure at r=R, on the surface
        self.p_surface = p_surface

        # Initialize star properties: radius and total mass
        self.star_radius = 0.0
        self.star_mass = 0.0

    def _ode_system(self, r, y):

        # ODE System that describes the interior structure of the star
        p = y[0]
        m = y[1]
        rho = self.rho(p)
        dp_dr = -((rho + p)*(m + 4*np.pi*r**3*p))/(r*(r - 2*m))         # TOV equation
        dm_dr = 4*np.pi*r**2*rho                                        # Rate of change of the mass function
        return [dp_dr, dm_dr]

    def _ode_termination_event(self, r, y):
        return y[0] - self.p_surface                # Condition of the event (event happens when condition == 0 ==> when p == p_surface)
    _ode_termination_event.terminal = True          # Set the event as a terminal event, terminating the integration of the ODE

    def solve_tov(self, r_begin=np.finfo(float).eps, r_end=np.inf, r_nsamples=10**6, method='RK45'):

        # Solve the ODE system
        ode_solution = solve_ivp(self._ode_system, [r_begin, r_end], [self.p_0, self.m_0], method=method, events=[self._ode_termination_event])
        r_ode_solution = ode_solution.t
        p_ode_solution = ode_solution.y[0]
        m_ode_solution = ode_solution.y[1]
        rho_ode_solution = self.rho(ode_solution.y[0])

        # Check the ODE solution status, and treat each case
        if ode_solution.status == -1:
            raise Exception(ode_solution.message)
        elif ode_solution.status == 0:
            raise Exception("The solver did not find the ODE termination event")
        elif ode_solution.status == 1:
            # Get the star radius and mass from the ODE termination event
            self.star_radius = ode_solution.t_events[0][0]
            self.star_mass = ode_solution.y_events[0][0][1]
            print(f"Star radius = {self.star_radius}")
            print(f"Star mass = {self.star_mass}")

        # Create interpolated functions for the solution using CubicSpline
        self.p_spline_function = CubicSpline(r_ode_solution, p_ode_solution)
        self.m_spline_function = CubicSpline(r_ode_solution, m_ode_solution)
        self.rho_spline_function = CubicSpline(r_ode_solution, rho_ode_solution)

        # Calculate the arrays for the solution according to the desired linspace
        self.r_space = np.linspace(r_begin, self.star_radius, r_nsamples)
        self.p_num_solution = self.p_spline_function(self.r_space)
        self.m_num_solution = self.m_spline_function(self.r_space)
        self.rho_num_solution = self.rho_spline_function(self.r_space)

    def plot_result(self):

        # Show simple plot of the solution
        plt.figure()
        plt.plot(self.r_space, self.p_num_solution, linewidth=1, label='pressure')
        plt.plot(self.r_space, self.m_num_solution, linewidth=1, label='mass function')
        plt.plot(self.r_space, self.rho_num_solution, linewidth=1, label='density')
        plt.title('TOV solution for the star')
        plt.xlabel('r')
        plt.legend()
        plt.show()


if __name__ == "__main__":

    # Set the EOS and pressure at the center and surface of the star
    def rho(p):
        c = 1.0e12          # [cm^2]
        return (np.abs(p/c))**(1/2)

    def p(rho):
        c = 1.0e12          # [cm^2]
        return c*rho**2

    rho_center = 2.376364e-13           # Center density in GU [cm^-2]
    p_center = rho(rho_center)          # Center pressure in GU [cm^-2]
    p_surface = 0.0

    # Define the object
    star_object = Star(rho, p_center, p_surface)

    # Solve the TOV equation
    star_object.solve_tov()

    # Plot the result
    star_object.plot_result()
