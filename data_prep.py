import numpy as np
import pandas as pd

from datetime import datetime
from ast import literal_eval
from sklearn.model_selection import train_test_split
from category_encoders import BinaryEncoder
from sklearn.preprocessing import MinMaxScaler


from utilities import load_config

np.random.seed(42)
config = load_config()


def drop_rows(df) -> pd.DataFrame:
    """
    Drop rows from Dataframe
    :param df: Dataframe
    :return: Dataframe without removed rows
    """
    df = df.drop(config.get('rows_to_drop'), axis=0)
    df = df.drop(df.loc[df['views'] <= 20000].index, axis=0)
    df = df.drop(df.loc[df['duration'] > 4200].index, axis=0)
    # drop talks with less than 3 topics
    num_topics_series = df['topics'].apply(literal_eval).apply(lambda row: len(row))
    df = df.drop(num_topics_series.loc[num_topics_series < 3].index)
    return df


def drop_columns(df) -> pd.DataFrame:
    """
    Drop unnecessary columns from Dataframe
    :param df: Dataframe
    :return: Dataframe without removed columns
    """
    df = df.drop(config.get('cols_to_drop'), axis=1)
    return df


def clean_event_column(df) -> pd.Series:
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
    mask = (df_subset.str.contains(r"Salon", na=False, regex=True))
    df_subset.loc[mask] = 'TedSalon'

    # change event name to 'Ted-Other' for each event that has less than 20 talks
    index_list = df_subset.groupby(df_subset).filter(lambda x: len(x) < 20).index
    df_subset.loc[index_list] = 'TED-Other'
    # for events that are very old
    df_subset.loc[(df_subset == 'EG') | (df_subset == 'TEDIndia')] = 'TED-Other'

    return df_subset


def clean_likes_column(num) -> int:
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


def clean_list_data_columns(df) -> pd.DataFrame:
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


def clean_published_date(df) -> pd.Series:
    """
    Convert datetime values to date
    :param df: original Dataframe
    :return: Series with clean 'published_date' values
    """
    series = df['published_date'].copy()
    series = pd.to_datetime(series).dt.date
    return series


def clean_data(df) -> pd.DataFrame:
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


def encode_topics_column(df) -> pd.DataFrame:
    """
    Create a column for each of 3 first topics in 'topics' column. \n
    Fit encoder on all unique values to avoid errors if unknown values are introduced. \n
    Encode 3 topic columns and concatenate to original Dataframe \n
    :param df: original Dataframe
    :return: Dataframe with encoded columns
    """
    topics_series = df['topics'].explode().unique()
    # create a dataframe with 3 same columns
    df_topics = pd.DataFrame(topics_series, columns=['topic_1'])
    df_topics['topic_2'] = df_topics['topic_1']
    df_topics['topic_3'] = df_topics['topic_1']

    # separate first 3 topics into columns
    for topic_num in range(0, 3):
        df[f'topic_{topic_num + 1}'] = df['topics'].apply(lambda array: array[topic_num])

    encoder = BinaryEncoder(cols=['topic_1', 'topic_2', 'topic_3'], return_df=True)
    # fit on df_topics to include all topics into encoder mapping
    encoder.fit(df_topics)
    df_topics = encoder.transform(df.loc[:, 'topic_1':'topic_3'])

    df = df.drop(columns=['topics', 'topic_1', 'topic_2', 'topic_3'])
    df = pd.concat([df, df_topics], axis=1)

    return df


def encode_event_column(df):
    """
    Use binary encoding for 'event' column. \n
    :param df: original Dataframe
    :return: Dataframe with 'event' column encoded
    """
    encoder = BinaryEncoder(cols=['event'], return_df=True)
    df = encoder.fit_transform(df)
    return df


def create_new_features(df):
    """
    Create new features by transforming existing features. \n
    Drop used features after transforming. \n
    :param df: original Dataframe
    :return: Dataframe with new features
    """
    df['title_length'] = df['title'].apply(lambda title: len(title))
    df['summary_length'] = df['summary'].apply(lambda summary: len(summary))
    df['num_subtitles'] = df['subtitle_languages'].apply(lambda array: len(array))
    # days passed since publication to the time when dataset was created
    df['days_passed'] = (config.get('dataset_creation_date') - pd.to_datetime(df['published_date']).dt.date).dt.days
    df['log_duration'] = df['duration'].apply(np.log)
    df['log_likes'] = df['likes'].apply(np.log)

    df = df.drop(columns=['title', 'summary', 'subtitle_languages', 'published_date', 'duration', 'likes'])
    return df


def split_data(df):
    """
    Split data into train and testing datasets. \n
    :param df: original Dataframe
    :return: training and testing dataset
    """
    X = df.drop(columns=['views'])
    y = df['views']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    return X_train, y_train, X_test, y_test


def scale_numerical_data(X_train, X_test):
    minmax_scaler = MinMaxScaler()
    # fit_transform on train data
    X_train[config.get('unscaled_num_columns')] = minmax_scaler.fit_transform(X_train[config.get('unscaled_num_columns')])
    # ONLY transform on test data!!!
    X_test[config.get('unscaled_num_columns')] = minmax_scaler.transform(X_test[config.get('unscaled_num_columns')])

    return X_train, X_test


# @TODO: Try using synthetic data to increase dataset size
def feature_engineering(df):
    df = encode_topics_column(df)
    df = encode_event_column(df)
    df = create_new_features(df)
    X_train, y_train, X_test, y_test = split_data(df)
    X_train, X_test = scale_numerical_data(X_train, X_test)
    print('Finished feature engineering.')
    return df
