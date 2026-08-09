import os
from pymongo import AsyncMongoClient


MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://localhost:27017"
)

mongo_client = AsyncMongoClient(MONGO_URL)

db = mongo_client.reminders_db
reminders_collection = db.reminders
