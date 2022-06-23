from pymongo.mongo_client import MongoClient

# my local mongodb server
host = 'localhost'
port = '27017'
connection_uri = f'mongodb://{host}:{port}/'

client = MongoClient(connection_uri)

