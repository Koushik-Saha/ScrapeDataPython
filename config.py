import os


class Config:
    """Flask configuration settings."""

    DEBUG = True  # Set to False in production

    uri = "mongodb+srv://koushiksaha666:hrZH3XWFJIWia2ct@bengaliblog.zwnix.mongodb.net/?retryWrites=true&w=majority&appName=BengaliBlog"

    # MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")  # Change for MongoDB Atlas
    # MONGO_URI = os.getenv("MONGO_URI", "mongodb://178.156.128.192:27017/")  # Change for MongoDB Atlas
    MONGO_URI = os.getenv("MONGO_URI", uri)  # Change for MongoDB Atlas
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")  # Allow CORS for frontend