import os
import math
import psutil
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import pandas as pd
from tqdm.contrib.concurrent import process_map
from constants import UnitConversion as uconv
from data_handling import dataframe_to_csv
from eos_library import QuarkEOS
from star_family_tides import DeformedStarFamily


# Constants
g0 = 930.0                                                      # Gibbs free energy per baryon of quark matter at null pressure [MeV]
alpha = ((1 / 3) - 8 / (3 * (1 + 2**(1 / 3))**3)) * g0**2       # alpha coefficient of the a2_max vs a4 curve [MeV^2]
a2_min = 0.0                                                    # Minimum a2 parameter value [MeV^2]
a2_max = alpha                                                  # Maximum a2 parameter value [MeV^2]
a4_min = 0.0                                                    # Minimum a4 parameter value [dimensionless]
a4_max = 1.0                                                    # Maximum a4 parameter value [dimensionless]
B_min = 0.0                                                     # Minimum B parameter value [MeV^4]
B_max = g0**4 / (108 * np.pi**2)                                # Maximum B parameter value [MeV^4]

# Observation data
M_max_inf_limit = 2.13                                          # Inferior limit of the maximum mass [solar mass] (Romani - 2 sigma)
R_canonical_inf_limit = 10.0                                    # Inferior limit of the radius of the canonical star [km]
R_canonical_sup_limit = 13.25                                   # Superior limit of the radius of the canonical star [km]
Lambda_canonical_sup_limit = 970.0                              # Superior limit of the tidal deformability of the canonical star [dimensionless] (Abbott - 2 sigma)


def calc_B_max(a2, a4):
    """Function that calculates the maximum B parameter value

    Args:
        a2 (array of float): a2 parameter of the EOS [MeV^2]
        a4 (array of float): a4 parameter of the EOS [dimensionless]

    Returns:
        array of float: Maximum B value [MeV^4]
    """
    return (g0**2 / (108 * np.pi**2)) * (g0**2 * a4 - 9 * a2)


def calc_B_min(a2, a4):
    """Function that calculates the minimum B parameter value

    Args:
        a2 (array of float): a2 parameter of the EOS [MeV^2]
        a4 (array of float): a4 parameter of the EOS [dimensionless]

    Returns:
        array of float: Minimum B value [MeV^4]
    """
    return (g0**2 / (54 * np.pi**2)) * ((4 * g0**2 * a4) / ((1 + 2**(1 / 3))**3) - 3 * a2)


def generate_strange_stars(mesh_size=21):
    """Function that generates a list of meshgrids representing the parameters of strange stars.
    This function also creates a dataframe with the parameters of strange stars

    Args:
        mesh_size (int, optional): Size of the mesh used to represent the parameters. Defaults to 21

    Returns:
        Arrays of float: Masked meshgrids representing the parameters
        Pandas dataframe of float: Dataframe with the parameters of strange stars
    """

    # Define the (a2, a4, B) rectangular meshgrid
    a2_1_2_range = np.linspace(a2_min**(1 / 2), a2_max**(1 / 2), mesh_size)
    a2_range = a2_1_2_range**2
    a4_range = np.linspace(a4_min, a4_max, mesh_size)
    B_1_4_range = np.linspace(B_min**(1 / 4), B_max**(1 / 4), mesh_size)
    B_range = B_1_4_range**4
    (a2, a4, B) = np.meshgrid(a2_range, a4_range, B_range)

    # Create the mesh masks according to each parameter minimum and maximum allowed values
    a2_max_mesh_mask = (a2 >= alpha * a4)
    a2_min_mesh_mask = (a2 <= a2_min)
    a4_max_mesh_mask = (a4 > a4_max)
    a4_min_mesh_mask = (a4 <= a4_min)
    B_max_mesh_mask = (B >= calc_B_max(a2, a4))
    B_min_mesh_mask = (B <= calc_B_min(a2, a4))

    # Create the combined mask and apply to each mesh grid
    mesh_mask = a2_max_mesh_mask | a2_min_mesh_mask | a4_max_mesh_mask | a4_min_mesh_mask | B_max_mesh_mask | B_min_mesh_mask
    a2_masked = np.ma.masked_where(mesh_mask, a2)
    a4_masked = np.ma.masked_where(mesh_mask, a4)
    B_masked = np.ma.masked_where(mesh_mask, B)

    # Loop over the mask and store the parameter points of the strange stars in a dataframe
    iterator = np.nditer(mesh_mask, flags=["multi_index"])
    parameter_points = []
    for x in iterator:
        if bool(x) is False:
            index = iterator.multi_index
            star_parameters = (a2[index]**(1 / 2), a4[index], B[index]**(1 / 4))
            parameter_points.append(star_parameters)
    parameter_dataframe = pd.DataFrame(parameter_points, columns=["a2^(1/2) [MeV]", "a4 [dimensionless]", "B^(1/4) [MeV]"])

    return (a2_masked, a4_masked, B_masked, parameter_dataframe)


def analyze_strange_star_family(dataframe_row):
    """Function that analyzes a star family, calculating the properties

    Args:
        dataframe_row (list): Row of the dataframe with the index and quark EOS parameters

    Returns:
        tuple: Tuple with index and star family properties calculated
    """

    # Unpack the row values
    (index, a2_1_2, a4, B_1_4, *_) = dataframe_row
    a2 = a2_1_2**2
    B = B_1_4**4

    # Create the EOS object
    quark_eos = QuarkEOS(a2, a4, B)

    # EOS analysis

    # Set the p_space
    max_rho = 1.0e16 * uconv.MASS_DENSITY_CGS_TO_GU         # Maximum density [m^-2]
    max_p = quark_eos.p(max_rho)                            # Maximum pressure [m^-2]
    p_space = max_p * np.logspace(-15.0, 0.0, 1000)

    # Check the EOS
    quark_eos.check_eos(p_space)

    # TOV and tidal analysis

    # Set the central pressure of the star
    rho_center = 1.0e16 * uconv.MASS_DENSITY_CGS_TO_GU      # Central density [m^-2]
    p_center = quark_eos.p(rho_center)                      # Central pressure [m^-2]

    # Set the p_center space that characterizes the star family
    p_center_space = p_center * np.logspace(-3.0, 0.0, 20)

    # Create the star family object
    star_family_object = DeformedStarFamily(quark_eos, p_center_space)

    # Find the maximum mass star
    star_family_object.find_maximum_mass_star()
    maximum_stable_rho_center = star_family_object.maximum_stable_rho_center
    maximum_mass = star_family_object.maximum_mass

    # Find the canonical star
    star_family_object.find_canonical_star()
    canonical_rho_center = star_family_object.canonical_rho_center
    canonical_radius = star_family_object.canonical_radius
    canonical_lambda = star_family_object.canonical_lambda

    # Find the maximum k2 star
    star_family_object.find_maximum_k2_star()
    maximum_k2_star_rho_center = star_family_object.maximum_k2_star_rho_center
    maximum_k2 = star_family_object.maximum_k2

    # Return the index and results
    return (index, maximum_stable_rho_center, maximum_mass, canonical_rho_center, canonical_radius, canonical_lambda, maximum_k2_star_rho_center, maximum_k2)


def analyze_strange_stars(parameter_dataframe):
    """Function that analyzes the strange stars given by the parameters in the dataframe, calculating the properties

    Args:
        parameter_dataframe (Pandas dataframe of float): Dataframe with the parameters of strange stars

    Returns:
        Pandas dataframe of float: Dataframe with the parameters and properties of strange stars
    """

    # Calculate the number of rows, number of processes and number of calculations per process (chunksize)
    n_rows = parameter_dataframe.shape[0]
    processes = psutil.cpu_count(logical=False)             # Number of processes are equal to the number of hardware cores
    chunksize = math.ceil(n_rows / (processes * 10))        # Create the chunksize smaller to provide some feedback on progress

    # Create a list with the rows of the dataframe
    rows_list = [list(row) for row in parameter_dataframe.itertuples()]

    # Execute the analysis for each row in parallel processes, using a progress bar from tqdm
    results = process_map(analyze_strange_star_family, rows_list, max_workers=processes, chunksize=chunksize)

    # Update the dataframe with the results
    for index, maximum_stable_rho_center, maximum_mass, canonical_rho_center, canonical_radius, canonical_lambda, maximum_k2_star_rho_center, maximum_k2 in results:
        parameter_dataframe.at[index, "rho_center_max [10^15 g ⋅ cm^-3]"] = maximum_stable_rho_center * uconv.MASS_DENSITY_GU_TO_CGS / 10**15
        parameter_dataframe.at[index, "M_max [solar mass]"] = maximum_mass * uconv.MASS_GU_TO_SOLAR_MASS
        parameter_dataframe.at[index, "rho_center_canonical [10^15 g ⋅ cm^-3]"] = canonical_rho_center * uconv.MASS_DENSITY_GU_TO_CGS / 10**15
        parameter_dataframe.at[index, "R_canonical [km]"] = canonical_radius / 10**3
        parameter_dataframe.at[index, "Lambda_canonical [dimensionless]"] = canonical_lambda
        parameter_dataframe.at[index, "rho_center_k2_max [10^15 g ⋅ cm^-3]"] = maximum_k2_star_rho_center * uconv.MASS_DENSITY_GU_TO_CGS / 10**15
        parameter_dataframe.at[index, "k2_max [dimensionless]"] = maximum_k2

    # Print and return the parameter dataframe at the end
    print(parameter_dataframe)
    return parameter_dataframe


def plot_parameter_points_scatter(a2, a4, B, figure_path="figures/app_quark_eos"):
    """Function that plots the scatter graph of the parameter points

    Args:
        a2 (3D array of float): Meshgrid with the a2 parameter of the EOS [MeV^2]
        a4 (3D array of float): Meshgrid with the a4 parameter of the EOS [dimensionless]
        B (3D array of float): Meshgrid with the B parameter of the EOS [MeV^4]
        figure_path (str, optional): Path used to save the figure. Defaults to "figures/app_quark_eos"
    """

    # Create figure and change properties
    (fig, ax) = plt.subplots(subplot_kw={"projection": "3d"}, figsize=(6.0, 4.5), constrained_layout=True)
    ax.set_title("Quark EOS parameter points", y=1.0, fontsize=11)
    ax.view_init(elev=15, azim=-115, roll=0)
    ax.set_xlim3d(a2_min**(1 / 2), a2_max**(1 / 2))
    ax.set_ylim3d(a4_min, a4_max)
    ax.set_zlim3d(B_min**(1 / 4), B_max**(1 / 4))
    ax.set_xlabel("$a_2^{1/2} ~ [MeV]$", fontsize=10, rotation=0)
    ax.set_ylabel("$a_4 ~ [dimensionless]$", fontsize=10, rotation=0)
    ax.set_zlabel("$B^{1/4} ~ [MeV]$", fontsize=10, rotation=90)
    ax.zaxis.set_rotate_label(False)

    # Add each scatter point
    ax.scatter(a2**(1 / 2), a4, B**(1 / 4))

    # Create the folder if necessary and save the figure
    os.makedirs(figure_path, exist_ok=True)
    figure_name = "quark_eos_parameter_points.svg"
    complete_path = os.path.join(figure_path, figure_name)
    plt.savefig(complete_path)

    # Show graph
    plt.show()


def plot_parameter_space(mesh_size=1000, figure_path="figures/app_quark_eos"):
    """Function that plots the graph of the parameter space

    Args:
        mesh_size (int, optional): Size of the mesh used to create the plot. Defaults to 1000
        figure_path (str, optional): Path used to save the figure. Defaults to "figures/app_quark_eos"
    """

    # Define the (a2, a4) rectangular meshgrid
    a2_range = np.linspace(a2_min, a2_max, mesh_size)
    a4_range = np.linspace(a4_min, a4_max, mesh_size)
    (a2, a4) = np.meshgrid(a2_range, a4_range)

    # Create the B_max and B_min surfaces
    B_max_surface = calc_B_max(a2, a4)
    B_min_surface = calc_B_min(a2, a4)

    # Apply the triangular mask to the meshgrid
    mesh_mask = (a2 > alpha * a4)
    a2_masked = np.ma.masked_where(mesh_mask, a2)
    a4_masked = np.ma.masked_where(mesh_mask, a4)
    B_max_surface_masked = np.ma.masked_where(mesh_mask, B_max_surface)
    B_min_surface_masked = np.ma.masked_where(mesh_mask, B_min_surface)

    # Create figure and change properties
    (fig, ax) = plt.subplots(subplot_kw={"projection": "3d"}, figsize=(6.0, 4.5), constrained_layout=True)
    ax.set_title("Quark EOS parameter space for stable strange stars", y=1.0, fontsize=11)
    ax.view_init(elev=15, azim=-115, roll=0)
    ax.set_xlim3d(a2_min**(1 / 2), a2_max**(1 / 2))
    ax.set_ylim3d(a4_min, a4_max)
    ax.set_zlim3d(B_min**(1 / 4), B_max**(1 / 4))
    ax.set_xlabel("$a_2^{1/2} ~ [MeV]$", fontsize=10, rotation=0)
    ax.set_ylabel("$a_4 ~ [dimensionless]$", fontsize=10, rotation=0)
    ax.set_zlabel("$B^{1/4} ~ [MeV]$", fontsize=10, rotation=90)
    ax.zaxis.set_rotate_label(False)

    # Add each surface plot
    a2_1_2_masked = a2_masked**(1 / 2)
    B_1_4_max_surface_masked = B_max_surface_masked**(1 / 4)
    B_1_4_min_surface_masked = B_min_surface_masked**(1 / 4)
    ax.plot_surface(a2_1_2_masked, a4_masked, B_1_4_max_surface_masked, cmap=cm.Reds, rstride=10, cstride=10, alpha=0.8, label="$B_{max}^{1/4}$")
    ax.plot_surface(a2_1_2_masked, a4_masked, B_1_4_min_surface_masked, cmap=cm.Blues, rstride=10, cstride=10, alpha=0.8, label="$B_{min}^{1/4}$")
    ax.legend(loc=(0.7, 0.25))

    # Add each contour plot (grey projections on each plane)
    ax.contourf(a2_1_2_masked, a4_masked, B_1_4_max_surface_masked, levels=0, zdir="x", offset=a2_max**(1 / 2), colors="gray", alpha=0.7, antialiased=True)
    ax.contourf(a2_1_2_masked, a4_masked, B_1_4_max_surface_masked, levels=0, zdir="y", offset=a4_max, colors="gray", alpha=0.7, antialiased=True)
    ax.contourf(a2_1_2_masked, a4_masked, B_1_4_max_surface_masked, levels=0, zdir="z", offset=0, colors="gray", alpha=0.7, antialiased=True)

    # Create the folder if necessary and save the figure
    os.makedirs(figure_path, exist_ok=True)
    figure_name = "quark_eos_parameter_space.svg"
    complete_path = os.path.join(figure_path, figure_name)
    plt.savefig(complete_path)

    # Show graph
    plt.show()


def plot_analysis_graphs(parameter_dataframe, figures_path="figures/app_quark_eos/analysis"):
    """Function that creates all the analysis graphs

    Args:
        parameter_dataframe (Pandas dataframe of float): Dataframe with the parameters of strange stars
        figures_path (str, optional): Path used to save the figures. Defaults to "figures/app_quark_eos/analysis".
    """

    # Create a dictionary with all the functions used in plotting, with each name and label description
    plot_dict = {
        "a2^(1/2)": {
            "name": "a2^(1/2)",
            "label": "$a_2^{1/2} ~ [MeV]$",
            "value": parameter_dataframe.loc[:, "a2^(1/2) [MeV]"],
        },
        "a4": {
            "name": "a4",
            "label": "$a_4 ~ [dimensionless]$",
            "value": parameter_dataframe.loc[:, "a4 [dimensionless]"],
        },
        "B^(1/4)": {
            "name": "B^(1/4)",
            "label": "$B^{1/4} ~ [MeV]$",
            "value": parameter_dataframe.loc[:, "B^(1/4) [MeV]"],
        },
        "M_max": {
            "name": "Maximum mass",
            "label": "$M_{max} ~ [M_{\\odot}]$",
            "unit": "$M_{\\odot}$",
            "value": parameter_dataframe.loc[:, "M_max [solar mass]"],
            "inf_limit": M_max_inf_limit,
            "sup_limit": None,
        },
        "R_canonical": {
            "name": "Canonical radius",
            "label": "$R_{canonical} ~ [km]$",
            "unit": "$km$",
            "value": parameter_dataframe.loc[:, "R_canonical [km]"],
            "inf_limit": R_canonical_inf_limit,
            "sup_limit": R_canonical_sup_limit,
        },
        "Lambda_canonical": {
            "name": "Canonical deformability",
            "label": "$\\log_{10} \\left( \\Lambda_{canonical} [dimensionless] \\right)$",
            "unit": "",
            "value": np.log10(parameter_dataframe.loc[:, "Lambda_canonical [dimensionless]"]),
            "inf_limit": None,
            "sup_limit": np.log10(Lambda_canonical_sup_limit),
        },
    }

    # Create a list with all the graphs to be plotted
    graphs_list = [
        ["a2^(1/2)", "M_max"],
        ["a4", "M_max"],
        ["B^(1/4)", "M_max"],
        ["a2^(1/2)", "R_canonical"],
        ["a4", "R_canonical"],
        ["B^(1/4)", "R_canonical"],
        ["a2^(1/2)", "Lambda_canonical"],
        ["a4", "Lambda_canonical"],
        ["B^(1/4)", "Lambda_canonical"],
    ]

    # Plot all graphs specified in graphs_list
    for (x_axis, y_axis) in graphs_list:

        # Create the plot
        plt.figure(figsize=(6.0, 4.5))
        plt.scatter(plot_dict[x_axis]["value"], plot_dict[y_axis]["value"], s=3**2)
        plt.title(f"{plot_dict[y_axis]["name"]} vs {plot_dict[x_axis]["name"]} graph of the Quark EOS", y=1.05, fontsize=11)
        plt.xlabel(plot_dict[x_axis]["label"], fontsize=10)
        plt.ylabel(plot_dict[y_axis]["label"], fontsize=10)

        # Add the y axis limit lines and legend
        ones_array = np.ones(2)
        x_axis_limits = np.array([np.min(plot_dict[x_axis]["value"]), np.max(plot_dict[x_axis]["value"])])
        if plot_dict[y_axis]["sup_limit"] is not None:
            label = f"Superior limit = {plot_dict[y_axis]["sup_limit"]:.2f} {plot_dict[y_axis]["unit"]}"
            plt.plot(x_axis_limits, plot_dict[y_axis]["sup_limit"] * ones_array, linewidth=1, color="#d62728", label=label)
        if plot_dict[y_axis]["inf_limit"] is not None:
            label = f"Inferior limit = {plot_dict[y_axis]["inf_limit"]:.2f} {plot_dict[y_axis]["unit"]}"
            plt.plot(x_axis_limits, plot_dict[y_axis]["inf_limit"] * ones_array, linewidth=1, color="#2ca02c", label=label)
        plt.legend()

        # Create the folder if necessary and save the figure
        os.makedirs(figures_path, exist_ok=True)
        x_axis_name = plot_dict[x_axis]["name"].lower().replace(" ", "_").replace("/", "_")
        y_axis_name = plot_dict[y_axis]["name"].lower().replace(" ", "_").replace("/", "_")
        figure_name = f"{y_axis_name}_vs_{x_axis_name}_graph.svg"
        complete_path = os.path.join(figures_path, figure_name)
        plt.savefig(complete_path)

    # Show graphs at the end
    plt.show()


def main():
    """Main logic
    """

    # Constants
    figure_path = "figures/app_quark_eos"                               # Path of the figures folder
    analysis_figures_path = os.path.join(figure_path, "analysis")       # Path of the analysis figures folder
    dataframe_csv_path = "results"                                      # Path of the results folder
    dataframe_csv_name = "quark_eos_analysis.csv"                       # Name of the csv file with the results
    parameter_space_mesh_size = 1001                                    # Number of points used in the meshgrid for the parameter space plot
    scatter_plot_mesh_size = 21                                         # Number of points used in the meshgrid for the scatter plot

    # Create the parameter space plot
    plot_parameter_space(parameter_space_mesh_size, figure_path)

    # Generate parameters for strange stars
    (a2_masked, a4_masked, B_masked, parameter_dataframe) = generate_strange_stars(scatter_plot_mesh_size)

    # Plot the parameter points generated for strange stars
    plot_parameter_points_scatter(a2_masked, a4_masked, B_masked, figure_path)

    # Analize the strange stars generated
    parameter_dataframe = analyze_strange_stars(parameter_dataframe)

    # Create all the analysis graphs
    plot_analysis_graphs(parameter_dataframe, analysis_figures_path)

    # Save the dataframe to a csv file
    dataframe_to_csv(dataframe=parameter_dataframe, file_path=dataframe_csv_path, file_name=dataframe_csv_name)


# This logic is only executed when this file is run directly in the command prompt
if __name__ == "__main__":
    main()
