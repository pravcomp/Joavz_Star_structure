import numpy as np
import matplotlib.pyplot as plt
from data_handling import *
from star_structure import Star
from star_family import StarFamily
from eos_library import TableEOS


# Open the .dat file with the expected radius-mass curve (units in solar mass and km)
expected_mass, expected_radius = dat_to_array(
    fname='data/MIR-GM1-HT-Local.dat',
    usecols=(0, 2))

# Create the EOS object
eos = TableEOS(fname='data/EOSFull_GM1_BPS.dat')

# Set the pressure at the center and surface of the star
p_center = eos.p_center     # Center pressure [m^-2]
p_surface = 1e-22           # Surface pressure [m^-2]

# Print the values used for p_center and p_surface
print(f"p_center = {p_center} [m^-2]")
print(f"p_surface = {p_surface} [m^-2]")

# Single star

# Define the object
star_object = Star(eos.rho, p_center, p_surface)

# Solve the TOV equation
star_object.solve_tov(max_step=100.0)

# Plot the star structure curves
star_object.plot_star_structure_curves()

# Star Family

# Set the p_center space that characterizes the star family
p_center_space = p_center * np.logspace(-4.7, 0.0, 50)

# Create the star family object
star_family_object = StarFamily(eos.rho, p_center_space, p_surface)

# Solve the TOV equation
star_family_object.solve_tov(max_step=100.0)

# Plot the calculated radius-mass curve
star_family_object.plot_radius_mass_curve(show_plot=False)

# Add the expected radius-mass curve to the plot, enable legend, and show the plot
plt.plot(expected_radius, expected_mass, linewidth=1, label="Expected curve")
plt.legend()
plt.show()
