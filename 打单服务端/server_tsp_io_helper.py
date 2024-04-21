import pandas as pd
import numpy as np


def read_tsp(filename):
    """
    Read a file in .tsp format into a pandas DataFrame

    The .tsp files can be found in the TSPLIB project. Currently, the library
    only considers the possibility of a 2D map.
    """
    with open(filename) as f:
        node_coord_start = None
        dimension = None
        lines = f.readlines()

        # Obtain the information about the .tsp
        i = 0
        while not dimension or not node_coord_start:
            line = lines[i]
            if line.startswith('DIMENSION :'):
                dimension = int(line.split()[-1])
            if line.startswith('NODE_COORD_SECTION'):
                node_coord_start = i
            i = i + 1

        print('Problem with {} cities read.'.format(dimension))

        f.seek(0)

        # Read a data frame out of the file descriptor
        cities = pd.read_csv(
            f,
            skiprows=node_coord_start + 1,
            sep=' ',
            names=['city', 'y', 'x'],
            dtype={'city': str, 'x': np.float64, 'y': np.float64},
            header=None,
            nrows=dimension
        )

        # cities.set_index('city', inplace=True)

        return cities


def read_tsp_from_data(dimension, nodes_data):
    """
    Create a pandas DataFrame from given dimension and nodes list
    dimension: An integer indicating the number of cities
    nodes_data: A list of tuples/lists where each contains city number, longitude, latitude
    """
    print('Problem with {} cities read.'.format(dimension))
    # Convert nodes_data into a DataFrame
    cities = pd.DataFrame(nodes_data, columns=['city', 'x', 'y'])  # 注意这里x,y的顺序和原代码中保持一致
    cities['city'] = cities['city'].astype(str)
    cities['x'] = cities['x'].astype(np.float64)
    cities['y'] = cities['y'].astype(np.float64)

    return cities


def normalize(points):
    """
    Return the normalized version of a given vector of points.

    For a given array of n-dimensions, normalize each dimension by removing the
    initial offset and normalizing the points in a proportional interval: [0,1]
    on y, maintining the original ratio on x.
    """
    ratio = (points.x.max() - points.x.min()) / (points.y.max() - points.y.min()), 1
    ratio = np.array(ratio) / max(ratio)
    norm = points.apply(lambda c: (c - c.min()) / (c.max() - c.min()))
    return norm.apply(lambda p: ratio * p, axis=1)
