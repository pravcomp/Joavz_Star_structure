import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from data_handling import *


class EOS:
    """Base class for the EOS classes
    """

    def plot(self, p_space):
        """Method that creates a graph of the EOS function given by rho(p)

        Args:
            p_space (array of float): Array that defines the plot interval [m^-2]
        """

        # Plot the EOS curve given by rho(p) and p(rho)
        plt.figure()
        plt.plot(p_space, self.rho(p_space), linewidth=1)
        plt.plot(self.p(self.rho(p_space)), self.rho(p_space), linewidth=1)
        plt.title(f"{self.__class__.__name__} curve")
        plt.xlabel('$p ~ [m^{-2}]$')
        plt.ylabel('$\\rho ~ [m^{-2}]$')
        plt.show()


class PolytropicEOS(EOS):
    """Class with the functions of the Polytropic EOS given by p = k * rho ** (1 + 1 / n)
    """

    def __init__(self, k, n):
        """Initialization method

        Args:
            k (float): Constant of proportionality of the EOS [m^2]
            n (float): Polytropic index [dimensionless]
        """
        self.k = float(k)
        self.m = 1.0 + 1.0 / float(n)

    def rho(self, p):
        """Function of the density in terms of the pressure

        Args:
            p (float): Pressure [m^-2]

        Returns:
            float: Density [m^-2]
        """
        return np.abs(p / self.k)**(1 / self.m)

    def p(self, rho):
        """Function of the pressure in terms of the density

        Args:
            rho (float): Density [m^-2]

        Returns:
            float: Pressure [m^-2]
        """
        return self.k * rho**self.m


class TableEOS(EOS):
    """Class with the functions of the EOS given by a table in a file, with density and pressure columns in CGS
    """

    def __init__(self, fname):
        """Initialization method

        Args:
            fname (string): File name of the table with the EOS (density and pressure columns)
        """

        # Open the .dat file with the EOS
        rho, p = dat_to_array(
            fname=fname,
            usecols=(0, 1),
            unit_conversion=(MASS_DENSITY_CGS_TO_GU, PRESSURE_CGS_TO_GU))

        # Convert the EOS to spline functions
        self.rho_spline_function = CubicSpline(p, rho, extrapolate=False)
        self.p_spline_function = CubicSpline(rho, p, extrapolate=False)

        # Save the center and surface density and pressure
        self.rho_center = rho[-1]
        self.p_center = p[-1]
        self.rho_surface = rho[0]
        self.p_surface = p[0]

    def rho(self, p):
        """Function of the density in terms of the pressure

        Args:
            p (float): Pressure [m^-2]

        Returns:
            float: Density [m^-2]
        """
        return self.rho_spline_function(p)

    def p(self, rho):
        """Function of the pressure in terms of the density

        Args:
            rho (float): Density [m^-2]

        Returns:
            float: Pressure [m^-2]
        """
        return self.p_spline_function(rho)


class QuarkEOS(EOS):
    """Class with the functions of the Quark EOS, defined by the grand thermodynamic potential given by:
    Omega = (3 / (4 * pi**2)) * (-a4 * mu**4 + a2 * mu**2) + B
    """

    def __init__(self, B, a2, a4):
        """Initialization method

        Args:
            B (float): Model free parameter [m^-2]
            a2 (float): Model free parameter [m^-1]
            a4 (float): Model free parameter [dimensionless]
        """
        self.B = B
        self.a2 = a2
        self.a4 = a4

    def rho(self, p):
        """Function of the density in terms of the pressure

        Args:
            p (float): Pressure [m^-2]

        Returns:
            float: Density [m^-2]
        """

        B = self.B
        a2 = self.a2
        a4 = self.a4

        rho = (
            3 * p + 4 * B + ((3 * a2**2) / (4 * np.pi**2 * a4)) * (
                1 + (1 + ((16 * np.pi**2 * a4) / (3 * a2**2)) * (p + B))**(1 / 2)
            )
        )

        return rho

    def p(self, rho):
        """Function of the pressure in terms of the density

        Args:
            rho (float): Density [m^-2]

        Returns:
            float: Pressure [m^-2]
        """

        B = self.B
        a2 = self.a2
        a4 = self.a4

        p = (
            (1 / 3) * (rho - 4 * B) - (a2**2 / (12 * np.pi**2 * a4)) * (
                1 + (1 + ((16 * np.pi**2 * a4) / a2**2) * (rho - B))**(1 / 2)
            )
        )

        return p


# This logic is a simple example, only executed when this file is run directly in the command prompt
if __name__ == "__main__":

    # Polytropic EOS test

    # Create the EOS object
    polytropic_eos = PolytropicEOS(k=1.0e8, n=1)

    # Calculate the center density and pressure
    rho_center = 2.376364e-9        # Center density [m^-2]

    p_center_calc = polytropic_eos.p(rho_center)
    rho_center_calc = polytropic_eos.rho(p_center_calc)

    # Print the result to check equations
    print(f"rho_center = {rho_center}")
    print(f"rho_center_calc = {rho_center_calc}")

    # Create a graph of the EOS function
    p_space = np.linspace(0.0, p_center_calc, 1000)
    polytropic_eos.plot(p_space)

    # Table EOS test

    # Create the EOS object
    table_eos = TableEOS(fname='data/EOSFull_GM1_BPS.dat')

    # Calculate the center density and pressure
    rho_center = table_eos.rho_center       # Center density [m^-2]

    p_center_calc = table_eos.p(rho_center)
    rho_center_calc = table_eos.rho(p_center_calc)

    # Print the result to check equations
    print(f"rho_center = {rho_center}")
    print(f"rho_center_calc = {rho_center_calc}")

    # Create a graph of the EOS function
    p_space = np.linspace(table_eos.p_surface, table_eos.p_center, 1000)
    table_eos.plot(p_space)

    # Quark EOS test

    # Create the EOS object (values chosen to build a strange star)
    B = 130 * MeV_fm3_to_SI * PRESSURE_SI_TO_GU
    a2 = (100 * MeV_fm3_to_SI * ENERGY_DENSITY_SI_TO_GU)**(1 / 2)
    a4 = 0.6
    quark_eos = QuarkEOS(B, a2, a4)

    # Calculate the center density and pressure
    rho_center = 2.376364e-9        # Center density [m^-2]

    p_center_calc = quark_eos.p(rho_center)
    rho_center_calc = quark_eos.rho(p_center_calc)

    # Print the result to check equations
    print(f"rho_center = {rho_center}")
    print(f"rho_center_calc = {rho_center_calc}")

    # Create a graph of the EOS function
    p_space = np.linspace(0.0, p_center_calc, 1000)
    quark_eos.plot(p_space)
