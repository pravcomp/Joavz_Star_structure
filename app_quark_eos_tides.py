import numpy as np
from data_handling import *
from star_family_tides import DeformedStarFamily
from eos_library import QuarkEOS


# Set the path of the figures
figures_path = "figures/app_quark_eos"

# Create the EOS object (values chosen to build a strange star)
a2 = 100**2     # [MeV^2]
a4 = 0.6        # [dimensionless]
B = 130**4      # [MeV^4]
eos = QuarkEOS(a2, a4, B)

# Set the pressure at the center and surface of the star
rho_center = 1.502e15 * MASS_DENSITY_CGS_TO_GU      # Central density [m^-2]
p_center = eos.p(rho_center)                        # Central pressure [m^-2]
p_surface = 0.0                                     # Surface pressure [m^-2]

# Set the p_center space that characterizes the star family
p_center_space = p_center * np.logspace(-4.0, 0.0, 50)

# Define the object
star_family_object = DeformedStarFamily(eos, p_center_space, p_surface)

# Solve the TOV equation and the tidal equation
star_family_object.solve_tidal(max_step=30.0)

# Plot all curves
star_family_object.plot_all_curves(figures_path)
