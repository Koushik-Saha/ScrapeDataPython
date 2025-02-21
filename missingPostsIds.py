from pymongo import MongoClient
import uuid

# ✅ Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update if MongoDB runs elsewhere
db = client["scraped_data"]  # Change to your database name
collection = db["posts"]  # Change to your collection name

# ✅ Find all documents where "id" field is missing
documents_without_id = collection.find({"id": {"$exists": False}})

# ✅ Iterate through each document and add a unique "id"
for doc in documents_without_id:
    unique_id = str(uuid.uuid4())  # Generate a unique UUID
    collection.update_one({"_id": doc["_id"]}, {"$set": {"id": unique_id}})
    print(f"✅ Added ID {unique_id} to document with _id: {doc['_id']}")

print("🚀 All missing IDs have been added successfully!")