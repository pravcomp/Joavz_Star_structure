from astropy import constants as const


# Unit conversion constants

# Universal constants in SI
MeV = 10**6 * const.e.si.value      # [J]
hbar = const.hbar.si.value          # [J ⋅ s]
c = const.c.si.value                # [m ⋅ s^-1]
G = const.G.si.value                # [m^3 ⋅ kg^-1 ⋅ s^-2]
M_sun = const.M_sun.si.value        # [kg]

# Conversion between SI and CGS
PRESSURE_SI_TO_CGS = 10
MASS_DENSITY_SI_TO_CGS = 10**(-3)

# Conversion between NU (with E = MeV) and SI
ENERGY_DENSITY_NU_TO_SI = MeV**4 * hbar**(-3) * c**(-3)
ENERGY_DENSITY_SI_TO_NU = ENERGY_DENSITY_NU_TO_SI**(-1)

# Conversion between GU and SI
ENERGY_DENSITY_GU_TO_SI = c**4 * G**(-1)
PRESSURE_GU_TO_SI = c**4 * G**(-1)
MASS_DENSITY_GU_TO_SI = c**2 * G**(-1)
MASS_GU_TO_SI = c**2 * G**(-1)
ENERGY_DENSITY_SI_TO_GU = ENERGY_DENSITY_GU_TO_SI**(-1)
PRESSURE_SI_TO_GU = PRESSURE_GU_TO_SI**(-1)
MASS_DENSITY_SI_TO_GU = MASS_DENSITY_GU_TO_SI**(-1)
MASS_SI_TO_GU = MASS_GU_TO_SI**(-1)

# Conversion between GU and CGS
PRESSURE_GU_TO_CGS = PRESSURE_GU_TO_SI * PRESSURE_SI_TO_CGS
MASS_DENSITY_GU_TO_CGS = MASS_DENSITY_GU_TO_SI * MASS_DENSITY_SI_TO_CGS
PRESSURE_CGS_TO_GU = PRESSURE_GU_TO_CGS**(-1)
MASS_DENSITY_CGS_TO_GU = MASS_DENSITY_GU_TO_CGS**(-1)

# Conversion between GU and NU
ENERGY_DENSITY_GU_TO_NU = ENERGY_DENSITY_GU_TO_SI * ENERGY_DENSITY_SI_TO_NU
ENERGY_DENSITY_NU_TO_GU = ENERGY_DENSITY_GU_TO_NU**(-1)

# Conversion between astronomical units and GU
MASS_SOLAR_MASS_TO_GU = M_sun * MASS_SI_TO_GU
MASS_GU_TO_SOLAR_MASS = MASS_SOLAR_MASS_TO_GU**(-1)
