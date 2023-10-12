import numpy as np
from data_handling import *
from perfect_fluid_star_family_tides import DeformedStarFamily
from eos_library import TableEOS


# Create the EOS object
eos = TableEOS(fname='data/SLy4.dat')

# Set the pressure at the center and surface of the star
rho_center = 2.2e-9             # Center density [m^-2]
p_center = eos.p(rho_center)    # Center pressure [m^-2]
p_surface = 1e-22               # Surface pressure [m^-2]

# Print the values used for p_center and p_surface
print(f"p_center = {p_center} [m^-2]")
print(f"p_surface = {p_surface} [m^-2]")

# Set the p_center space that characterizes the star family
p_center_space = p_center * np.logspace(-3.0, 0.0, 50)

# Create the star family object
star_family_object = DeformedStarFamily(eos.rho, p_center_space, p_surface)

# Solve the TOV equation, and the tidal equation
star_family_object.solve_tidal(max_step=100.0)

# Show the mass-radius curve
star_family_object.plot_mass_radius_curve()

# Show the derivative of the mass with respect to rho_center curve
star_family_object.plot_dm_drho_center_curve()

# Show the center pressure curve
star_family_object.plot_p_center_curve()

# Plot the calculated k2 curve
star_family_object.plot_k2_curve()

# Show the k2 vs p_center curve
star_family_object.plot_k2_p_center_curve()
