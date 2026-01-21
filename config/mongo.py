from pymongo import MongoClient


def create_mongo_client(mongo_url: str, db_name: str):
    client = MongoClient(
        mongo_url,
        maxPoolSize=50,
        minPoolSize=1,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000,
        retryWrites=True,
    )
    db = client[db_name]
    return client, db
