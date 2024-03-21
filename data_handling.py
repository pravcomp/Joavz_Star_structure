import os
import matplotlib.pyplot as plt
import numpy as np


def csv_to_arrays(file_name="file_name.csv", usecols=(0, 1), unit_conversion=(1.0, 1.0)):
    """Converts data in a .csv file into numpy arrays

    Args:
        file_name (str, optional): Name of the .csv file, including the path. Defaults to "file_name.csv"
        usecols (tuple, optional): Set the column numbers to read in the .csv file. Defaults to (0, 1)
        unit_conversion (tuple, optional): Conversion multiplicative factor for each column. Defaults to (1.0, 1.0)

    Returns:
        tuple of arrays: Numpy arrays with the data read from the .csv file
    """

    (x, y) = np.loadtxt(fname=file_name, delimiter=",", skiprows=1, usecols=usecols, unpack=True)
    (x_converted, y_converted) = (x * unit_conversion[0], y * unit_conversion[1])

    return (x_converted, y_converted)


def dataframe_to_csv(dataframe, file_path="results", file_name="dataframe.csv"):
    """Saves a dataframe to a csv file

    Args:
        dataframe (pandas dataframe): Dataframe to be saved
        file_path (str, optional): Path of the file to be created. Defaults to "results"
        file_name (str, optional): Name of the file to be created. Defaults to "dataframe.csv"
    """

    os.makedirs(file_path, exist_ok=True)
    complete_path = os.path.join(file_path, file_name)
    dataframe.to_csv(complete_path, index=False)


def main():
    """Main logic
    """

    # Open an example .csv file
    (radius, mass) = csv_to_arrays("data/BSk20_M_vs_R.csv")

    # Plot the curve given in the example .csv file
    plt.figure(figsize=(6.0, 4.5))
    plt.plot(radius, mass, linewidth=1, marker=".")
    plt.title("BSk20 EOS M vs R from .csv file", y=1.05, fontsize=11)
    plt.xlabel("$R ~ [km]$", fontsize=10)
    plt.ylabel("$M ~ [M_{\\odot}]$", fontsize=10)
    plt.show()


# This logic is only executed when this file is run directly in the command prompt
if __name__ == "__main__":
    main()
