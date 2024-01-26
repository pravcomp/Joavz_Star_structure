from time import perf_counter
import numpy as np
from scipy.interpolate import CubicSpline
from constants import DefaultValues as dval
from constants import UnitConversion as uconv
from eos_library import PolytropicEOS
from star_family_structure import StarFamily
from star_tides import DeformedStar


class DeformedStarFamily(StarFamily):
    """Class with all the properties and methods necessary to describe a family of deformed stars

    Args:
        StarFamily (class): Parent class with all the properties and methods necessary to describe a family of stars
        Each star in the family is characterized by a specific value of central pressure (p_center)
    """

    def __init__(self, eos, p_center_space, p_surface=dval.P_SURFACE, r_init=dval.R_INIT, r_final=dval.R_FINAL, method=dval.IVP_METHOD,
                 max_step=dval.MAX_STEP, atol_tov=dval.ATOL_TOV, atol_tidal=dval.ATOL_TIDAL, rtol=dval.RTOL):
        """Initialization method

        Args:
            eos (object): Python object with methods rho, p, drho_dp, and dp_drho that describes the EOS of the stars
            p_center_space (array of float): Array with the central pressure of each star in the family [m^-2]
            p_surface (float, optional): Surface pressure of the stars [m^-2]. Defaults to P_SURFACE
            r_init (float, optional): Initial radial coordinate r of the IVP solve [m]. Defaults to R_INIT
            r_final (float, optional): Final radial coordinate r of the IVP solve [m]. Defaults to R_FINAL
            method (str, optional): Method used by the IVP solver. Defaults to IVP_METHOD
            max_step (float, optional): Maximum allowed step size for the IVP solver [m]. Defaults to MAX_STEP
            atol_tov (float or array of float, optional): Absolute tolerance of the IVP solver for the TOV system. Defaults to ATOL_TOV
            atol_tidal (float, optional): Absolute tolerance of the IVP solver for the tidal system. Defaults to ATOL_TIDAL
            rtol (float, optional): Relative tolerance of the IVP solver. Defaults to RTOL
        """

        # Execute parent class' __init__ method
        super().__init__(eos, p_center_space, p_surface, r_init, r_final, method, max_step, atol_tov, rtol)

        # Store the input parameters
        self.atol_tidal = atol_tidal

        # Create a star object with the first p_center value, using instead the DeformedStar class
        self.star_object = DeformedStar(eos, self.p_center_space[0], p_surface, r_init, r_final, method, max_step, atol_tov, atol_tidal, rtol)

        # Initialize deformed star family properties
        self.k2_array = np.zeros(self.p_center_space.size)      # Array with the tidal Love numbers of the stars [dimensionless]
        self.maximum_k2_star_rho_center = self.MAX_RHO          # Central density of the star with the maximum k2 [m^-2]
        self.maximum_k2 = np.inf                                # Maximum k2 of the star family [dimensionless]

    def _config_plot(self):

        # Execute parent class' _config_plot method
        super()._config_plot()

        # Add new functions to the plot dictionary
        self.plot_dict["k2"] = {
            "name": "Love number",
            "label": "$k2 ~ [dimensionless]$",
            "value": self.k2_array,
        }

        # Add new curves to be plotted on the list
        extra_curves_list = [
            ["rho_c", "k2"],
            ["R", "k2"],
            ["M", "k2"],
            ["C", "k2"],
        ]
        self.curves_list += extra_curves_list

    def _calc_maximum_k2_star(self):
        """Method that calculates the maximum k2 star properties
        """

        # Create the k2 vs rho_center interpolated function and calculate its derivative
        k2_rho_center_spline = CubicSpline(self.rho_center_space, self.k2_array, extrapolate=False)
        dk2_drho_center_spline = k2_rho_center_spline.derivative()

        # Calculate the maximum k2 star rho_center and mass
        dk2_drho_center_roots = dk2_drho_center_spline.roots()
        if dk2_drho_center_roots.size > 0:
            self.maximum_k2_star_rho_center = dk2_drho_center_roots[0]
            self.maximum_k2 = k2_rho_center_spline(self.maximum_k2_star_rho_center)

        # Return the calculated rho_center
        return self.maximum_k2_star_rho_center

    def find_maximum_k2_star(self):
        """Method that finds the maximum k2 star

        Raises:
            ValueError: Exception in case the initial radial coordinate is too large
            RuntimeError: Exception in case the IVP fails to solve the equation
            RuntimeError: Exception in case the IVP fails to find the ODE termination event
        """

        self._find_star(self._calc_maximum_k2_star, self.solve_combined_tov_tidal, self.maximum_stable_rho_center)

    def solve_combined_tov_tidal(self, show_results=True):
        """Method that solves the combined TOV+tidal system for each star in the family, finding p, m, nu, and k2

        Args:
            show_results (bool, optional): Flag that enables the results printing after the solve. Defaults to True

        Raises:
            ValueError: Exception in case the initial radial coordinate is too large
            RuntimeError: Exception in case the IVP fails to solve the equation
            RuntimeError: Exception in case the IVP fails to find the ODE termination event
        """

        # Reinitialize the k2 array with the right size
        self.k2_array = np.zeros(self.p_center_space.size)

        # Solve the combined TOV+tidal system for each star in the family
        start_time = perf_counter()
        for k, p_center in enumerate(self.p_center_space):
            self.star_object.solve_combined_tov_tidal(p_center, False)
            self.radius_array[k] = self.star_object.star_radius
            self.mass_array[k] = self.star_object.star_mass
            self.k2_array[k] = self.star_object.k2
        self.execution_time = perf_counter() - start_time

        # Configure the plot
        self._config_plot()

        # Show results if requested
        if show_results is True:
            self.print_results()

    def print_results(self):
        """Method that prints the results found
        """

        # Execute parent class' print_results method
        super().print_results()

        # Calculate the star family properties
        self._calc_maximum_k2_star()

        # Print the results
        print(f"Maximum k2 (k2_max) = {(self.maximum_k2):e} [dimensionless]")
        print(f"Maximum k2 star central density (rho_center_k2_max) = {(self.maximum_k2_star_rho_center * uconv.MASS_DENSITY_GU_TO_CGS):e} [g ⋅ cm^-3]")


def main():
    """Main logic
    """

    # Constants
    MAX_RHO = 5.691e15 * uconv.MASS_DENSITY_CGS_TO_GU       # Maximum density [m^-2]
    STARS_LOGSPACE = np.logspace(-5.0, 0.0, 50)             # Logspace used to create the star family

    # EOS parameters
    k = 1.0e8       # Proportional constant [dimensionless]
    n = 1           # Polytropic index [dimensionless]

    # Create the EOS object
    eos = PolytropicEOS(k, n)

    # Set the central pressure of the star and p_center space of the star family
    rho_center = MAX_RHO                # Central density [m^-2]
    p_center = eos.p(rho_center)        # Central pressure [m^-2]
    p_center_space = p_center * STARS_LOGSPACE

    # Create the star family object
    star_family_object = DeformedStarFamily(eos, p_center_space)

    # Solve the combined TOV+tidal system and plot all curves
    star_family_object.solve_combined_tov_tidal()
    star_family_object.plot_all_curves()


# This logic is only executed when this file is run directly in the command prompt
if __name__ == "__main__":
    main()
