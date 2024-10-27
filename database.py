from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve MongoDB URI from environment variable
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['trading_tracker_db']  # Replace with your database name

# Collections
users_collection = db['users']  # Replace with collection names as needed

# Optional: Helper function for database operations (if needed)
def add_user(name, contact, hashed_password):
    user_data = {
        'name': name,
        'contact': contact,
        'password': hashed_password
    }
    result = users_collection.insert_one(user_data)
    return result.inserted_id

def find_user_by_contact(contact):
    return users_collection.find_one({'contact': contact})

# Add any other helper functions for database operations here
