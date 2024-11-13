import pandas as pd
import numpy as np

def metadata_and_data_to_csv(metadata, data, path):
    """
    Convinience function that takes two arbitrary dataframes and writes them to a csv one below the other with a space in between.
    Used nominally for a 1XN metadata df and a data df

    :param metadata: dataframe containing metadata, standard is a 1XN table (many columns with one value each)
    :param data: dataframe containing time data captured from measurment, appended to csv below metadata
    :param path: path to save csv in
    """

    metadata.to_csv(path, index=False, header=True)

    # Add a blank line to the CSV file
    with open(path, 'a') as f:
        f.write('\n')

    # Append data to the same CSV file with its own header
    data.to_csv(path, mode='a', index=False, header=True)

def standard_csv_to_metadata_and_data(path, metadata_header_row=0, data_header_row=2):
    """
    Convinience function that takes the piec standard 1xN metadata with data below and returns each as individual dataframes

    :param path: path to save csv in
    :param metadata_header_row: row where metadata starts (defaut row 0)
    :param data_header_row:  row where data starts (defaut row 2)
    """
    # Read metadata using its header row and assuming it has only one row of data
    metadata = pd.read_csv(path, header=metadata_header_row, nrows=1)

    # Read data starting from its header row and continuing to the end of the file
    data = pd.read_csv(path, header=data_header_row)

    return metadata, data