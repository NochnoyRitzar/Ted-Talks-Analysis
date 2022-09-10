from utilities import load_data
from data_prep import clean_data


if __name__ == '__main__':
    df = load_data('data/raw/talks_info.csv')
    df = clean_data(df)
    print('Work complete')
