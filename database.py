from pymongo import MongoClient
MONGO_URL = "mongodb+srv://purvakhandekar1208_db_user:pmk123@cluster0.mmcylr7.mongodb.net/?appName=Cluster0"

client = MongoClient("mongodb+srv://purvakhandekar1208_db_user:pmk123@cluster0.mmcylr7.mongodb.net/?appName=Cluster0")

db = client["travelDB"]

users_collection = db["users"]
flights_collection = db["flights"]
bookings_collection = db["bookings"]