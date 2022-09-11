from ast import literal_eval

import numpy as np
import pandas as pd

from utilities import load_config

np.random.seed(42)
config = load_config()


def drop_rows(df):
    """
    Drop rows from Dataframe
    :param df: Dataframe
    :return: Dataframe without removed rows
    """
    df = df.drop(config.get('rows_to_drop'), axis=0)
    return df


def drop_columns(df):
    """
    Drop unnecessary columns from Dataframe
    :param df: Dataframe
    :return: Dataframe without removed columns
    """
    df = df.drop(config.get('cols_to_drop'), axis=1)
    return df


def clean_event_column(df):
    """
    Remove date from events and group with similar. \n
    Change name to 'TED-Other' for events with low talk count
    :param df: original Dataframe
    :return: Series with processed values
    """
    df_subset = df['event'].copy()

    # change all occurences of 'TED2021', 'TED2016' to just 'TED'
    df_subset.loc[df_subset.str.contains(r"TED\d{4}", regex=True)] = 'TED'

    # remove year number from events essentially grouping them
    mask = (df_subset.str.contains(r"\s\d{4}", regex=True))
    df_subset.loc[mask] = df_subset.loc[mask].apply(lambda event_name: event_name[:-5])
    mask = (df_subset.str.contains(r"NY\d{4}", regex=True))
    df_subset.loc[mask] = df_subset.loc[mask].apply(lambda event_name: event_name[:-4])

    # change event name to 'Ted-Other' for each event that has less than 20 talks
    index_list = df_subset.groupby(df_subset).filter(lambda x: len(x) < 20).index
    df_subset.loc[index_list] = 'TED-Other'

    return df_subset


def clean_likes_column(num):
    """
    Returns integer number from string
    :param num: number in string format
    :type num: str
    :rtype: int
    """
    if num[-1] == 'K':
        num = float(num[:-1]) * 1000
        if num >= 100000:
            # to get a bit of randomness in data
            num += np.random.randint(1, 1000)
        else:
            num += np.random.randint(1, 100)
    elif num[-1] == 'M':
        num = float(num[:-1]) * 1000000 + np.random.randint(1000, 10000)

    return int(num)


def clean_list_data_columns(df):
    """
    Convert string values to python objects(dict and list), unpack dictionaries and group into list of topics \n
    :param df: original Dataframe
    :return: processed Dataframe subset
    """
    df_list_data = df.loc[:, config.get('cols_with_list_data')].copy()
    for col in df_list_data.columns:
        df_list_data[col] = df_list_data[col].apply(literal_eval)
        series = df_list_data[col].explode()
        series = series.apply(lambda x: x.get('name') if not isinstance(x, float) else None)
        df_list_data[col] = series.groupby(series.index).agg(list)

    return df_list_data


def clean_published_date(df):
    """
    Convert datetime values to date
    :param df: original Dataframe
    :return: Series with clean 'published_date' values
    """
    series = df['published_date'].copy()
    series = pd.to_datetime(series).dt.date
    return series


def clean_data(df):
    """
    Contains all functions that are related to cleaning raw data.
    :param df: Dataframe with raw data
    :return: clean Dataframe
    """
    df = drop_columns(df)
    df = drop_rows(df)
    df['event'] = clean_event_column(df)
    df['likes'] = df['likes'].apply(clean_likes_column)
    df.loc[:, config.get('cols_with_list_data')] = clean_list_data_columns(df)
    df['published_date'] = clean_published_date(df)
    df.to_csv('data/intermediate/clean_data.csv', index=False)

    print('Finished cleaning raw data. Saved intermediate result to corresponding folder')

    return df
