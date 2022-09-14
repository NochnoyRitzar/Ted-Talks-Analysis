from utilities import load_data
from data_prep import clean_data, feature_engineering


if __name__ == '__main__':
    df = load_data('data/raw/talks_info.csv')
    df = clean_data(df)
    # df = feature_engineering(df)
    print('Work complete')
