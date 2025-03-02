import time
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from urllib.parse import unquote
from pymongo.errors import DuplicateKeyError

# Import custom scraper functions
from scraper import scrape_homepage
from scraperDetails import scrape_post_details
from scraperCategoryList import scrape_category_posts
from scraperCategoryListName import extract_categories

# ✅ Import Configuration
from config import Config

from pymongo.mongo_client import MongoClient

# ✅ Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)  # Load config settings

# ✅ Enable CORS for frontend
CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})

# ✅ Connect to MongoDB using `MONGO_URI`
client = MongoClient(app.config["MONGO_URI"])

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["scraped_data"]
collection = db["posts"]
posts_details_collection = db["postsDetails"]

# ✅ Function to convert MongoDB documents to JSON safely
def serialize_doc(doc):
    """Convert MongoDB ObjectId to string before returning JSON."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


@app.route('/scrape-homepage', methods=['GET'])
def scrape_home():
    """API endpoint to get paginated posts."""
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=15, type=int)

    if limit > 15:
        return jsonify({"error": "Limit cannot be greater than 15"}), 400

    data = scrape_homepage(page=page, limit=limit)

    if "posts" in data:
        data["posts"] = [serialize_doc(post) for post in data["posts"]]

    return jsonify(data)


@app.route('/get-stored-homepage', methods=['GET'])
def get_stored_homepage():
    posts = list(collection.find({}, {"_id": 1, "title": 1, "url": 1, "author": 1, "date": 1, "views": 1, "subtitle": 1,
                                      "category": 1, "tags": 1}))
    posts_serialized = [serialize_doc(post) for post in posts]
    return jsonify({"total_posts": len(posts_serialized), "posts": posts_serialized})


@app.route('/get-posts', methods=['GET'])
def get_posts():
    """Fetch posts with pagination"""
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 15))

        skip = (page - 1) * limit
        posts_cursor = collection.find({}, {"_id": 0}).skip(skip).limit(limit)
        posts = list(posts_cursor)

        total_posts = collection.count_documents({})
        total_pages = (total_posts + limit - 1) // limit

        return jsonify({
            "data": posts,
            "pagination": {
                "current_page": page,
                "limit": limit,
                "total_posts": total_posts,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/scrape-post', methods=['GET'])
def scrape_post_api():
    """API to scrape and save posts, preventing duplicate errors"""
    url = request.args.get('url')

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    if not unquote(url).isascii():
        return jsonify({"error": "Non-ASCII URL skipped"}), 400

    existing_post = posts_details_collection.find_one({"url": url})
    if existing_post:
        return jsonify({
            "data": serialize_doc(existing_post),
            "message": "Post already exists"
        }), 200

    post_data = scrape_post_details(url)

    if not post_data:
        time.sleep(3)
        existing_post = posts_details_collection.find_one({"url": url})
        if existing_post:
            return jsonify({
                "data": serialize_doc(existing_post),
                "message": "Post already exists after retry"
            }), 200
        return jsonify({"error": "Scraping function returned None"}), 500

    if "post_id" not in post_data or not post_data["post_id"]:
        return jsonify({"error": "Scraped data is missing 'post_id' key"}), 500

    try:
        if posts_details_collection.find_one({"post_id": post_data["post_id"]}):
            return jsonify({
                "data": serialize_doc(existing_post),
                "message": "Post already exists"
            }), 200

        result = posts_details_collection.insert_one(post_data)
        post_data["_id"] = str(result.inserted_id)
        return jsonify({
            "data": post_data,
            "message": "Post successfully saved"
        }), 201

    except Exception as e:
        if "E11000" in str(e):
            existing_post = posts_details_collection.find_one({"url": post_data["url"]})
            return jsonify({
                "data": serialize_doc(existing_post),
                "message": "Post already exists"
            }), 200
        return jsonify({"error": str(e)}), 500


@app.route('/scrape-category', methods=['GET'])
def scrape_category_api():
    """API endpoint to scrape category-wise posts."""
    category_url = request.args.get("url")
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=15, type=int)

    if not category_url:
        return jsonify({"error": "Category URL parameter is required"}), 400

    post_data = scrape_category_posts(category_url, page, limit)
    return jsonify(post_data)


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """API endpoint to get categories with URLs and post counts."""
    url = request.args.get('url')

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    categories = extract_categories(url)
    return jsonify(categories)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)