import os


class Config:
    """Flask configuration settings."""

    DEBUG = True  # Set to False in production
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/scraped_data")  # Change for MongoDB Atlas
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")  # Allow CORS for frontend