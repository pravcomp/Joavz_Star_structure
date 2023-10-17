import numpy as np
from data_handling import *
from star_structure import Star
from star_family import StarFamily
from eos_library import QuarkEOS


# Set the figures path
figures_path = "figures/app_quark_eos"

# Create the EOS object (values chosen to build a strange star)
B = 130**4 * ENERGY_DENSITY_NU_TO_GU
a2 = (100**4 * ENERGY_DENSITY_NU_TO_GU)**(1 / 2)
a4 = 0.6
eos = QuarkEOS(B, a2, a4)

# Print the values used for B, a2, and a4
print(f"B = {B} [m^-2]")
print(f"a2 = {a2} [m^-1]")
print(f"a4 = {a4} [dimensionless]")

# Set the pressure at the center and surface of the star
rho_center = 1.2e-9             # Center density [m^-2]
p_center = eos.p(rho_center)    # Center pressure [m^-2]
p_surface = 0.0                 # Surface pressure [m^-2]

# Print the values used for p_center and p_surface
print(f"p_center = {p_center} [m^-2]")
print(f"p_surface = {p_surface} [m^-2]")

# Single star

# Define the object
star_object = Star(eos.rho, p_center, p_surface)

# Solve the TOV equation
star_object.solve_tov(max_step=10.0)

# Plot the star structure curves
star_object.plot_star_structure_curves(figures_path)

# Star Family

# Set the p_center space that characterizes the star family
p_center_space = p_center * np.logspace(-5.0, 0.0, 50)

# Define the object
star_family_object = StarFamily(eos.rho, p_center_space, p_surface)

# Solve the TOV equation
star_family_object.solve_tov(max_step=10.0)

# Plot all curves
star_family_object.plot_all_curves(figures_path)
