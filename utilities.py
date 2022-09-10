import pandas as pd
from yaml import safe_load


def load_data(path):
    """
    Load raw data from csv file into pandas Dataframe
    :param path: path to .csv file
    :return: Dataframe
    """
    df = pd.read_csv(path)
    print('Data loaded')
    return df


def load_config():
    """
    Load configuration from yaml file
    :return: config
    """
    with open('config/config.yaml') as file:
        config = safe_load(file)
    return config
