import time

from bson.json_util import dumps

from flask import Flask, request, jsonify
from pymongo.errors import DuplicateKeyError

from scraper import scrape_homepage
from scraperDetails import scrape_post_details
from scraperCategoryList import scrape_category_posts
from scraperCategoryListName import extract_categories
from pymongo import MongoClient
from bson import ObjectId  # ✅ Import BSON for ObjectId
from urllib.parse import unquote
from flask_cors import CORS

app = Flask(__name__)

# ✅ Allow CORS only for requests from Next.js frontend (localhost:3000)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


# ✅ Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Change if using MongoDB Atlas
db = client["scraped_data"]
collection = db["posts"]
posts_details_collection = db["postsDetails"]


# ✅ Function to convert MongoDB documents to JSON safely
def serialize_doc(doc):
    """Convert MongoDB ObjectId to string before returning JSON."""
    if "_id" in doc:  # ✅ Check if '_id' exists before conversion
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

    # ✅ Convert MongoDB ObjectId to string only if '_id' exists
    if "posts" in data:
        data["posts"] = [serialize_doc(post) for post in data["posts"]]

    return jsonify(data)


# ✅ Function to convert MongoDB documents to JSON
def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
    return doc


@app.route('/get-stored-homepage', methods=['GET'])
def get_stored_homepage():
    posts = list(collection.find({}, {"_id": 1, "title": 1, "url": 1, "author": 1, "date": 1, "views": 1, "subtitle": 1,
                                      "category": 1, "tags": 1}))

    # ✅ Convert all documents before returning
    posts_serialized = [serialize_doc(post) for post in posts]

    return jsonify({"total_posts": len(posts_serialized), "posts": posts_serialized})


@app.route('/get-posts', methods=['GET'])
def get_posts():
    """Fetch posts with pagination"""
    try:
        page = int(request.args.get("page", 1))  # Default: page 1
        limit = int(request.args.get("limit", 15))  # Default: 15 posts

        skip = (page - 1) * limit
        posts_cursor = collection.find({}, {"_id": 0}).skip(skip).limit(limit)
        posts = list(posts_cursor)

        total_posts = collection.count_documents({})
        total_pages = (total_posts + limit - 1) // limit  # Ceiling division

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


def serialize_mongo_doc(doc):
    """✅ Convert MongoDB document to JSON serializable format"""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
    return doc


def is_valid_url(url):
    """✅ Returns False if the URL contains non-ASCII characters, else True"""
    decoded_url = unquote(url)  # Decode percent-encoded characters
    return decoded_url.isascii()  # Check if all characters are ASCII


@app.route('/scrape-post', methods=['GET'])
def scrape_post_api():
    """API to scrape and save posts, preventing duplicate errors"""
    url = request.args.get('url')

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    # ✅ Skip URLs with non-ASCII characters
    if not is_valid_url(url):
        print(f"⚠️ Skipping non-ASCII URL: {url}")
        return jsonify({"error": "Non-ASCII URL skipped"}), 400  # ✅ Fixed `continue` issue

    # ✅ Check if post already exists
    existing_post = posts_details_collection.find_one({"url": url})
    if existing_post:
        return jsonify({
            "data": serialize_mongo_doc(existing_post),
            "message": "Post already exists"
        }), 200

    # ✅ Scrape Post Data
    post_data = scrape_post_details(url)  # Your scraping function

    # 🚨 If scraping failed, retry checking for data
    if not post_data:
        time.sleep(3)  # ⏳ Wait 3 seconds before retrying
        existing_post = posts_details_collection.find_one({"url": url})
        if existing_post:
            return jsonify({
                "data": serialize_mongo_doc(existing_post),
                "message": "Post already exists after retry"
            }), 200
        return jsonify({"error": "Scraping function returned None"}), 500

    # 🚨 If `post_id` is missing in the scraped data
    if "post_id" not in post_data or not post_data["post_id"]:
        return jsonify({"error": "Scraped data is missing 'post_id' key"}), 500

    try:
        # ✅ Check again before inserting (avoiding race conditions)
        if posts_details_collection.find_one({"post_id": post_data["post_id"]}):
            return jsonify({
                "data": serialize_mongo_doc(existing_post),
                "message": "Post already exists"
            }), 200

        result = posts_details_collection.insert_one(post_data)
        post_data["_id"] = str(result.inserted_id)  # ✅ Convert ObjectId to string
        return jsonify({
            "data": post_data,
            "message": "Post successfully saved"
        }), 201

    except Exception as e:
        if "E11000" in str(e):  # ✅ Catch duplicate key error and return gracefully
            existing_post = posts_details_collection.find_one({"url": post_data["url"]})
            return jsonify({
                "data": serialize_mongo_doc(existing_post),
                "message": "Post already exists"
            }), 200
        return jsonify({"error": str(e)}), 500


@app.route('/get-scrape-post-data', methods=['GET'])
def get_post():
    """Fetch post details using URL, Title, ID, or post_id."""

    title = request.args.get('title')
    url = request.args.get('url')
    id_ = request.args.get('id')  # `id` from `posts`
    post_id = request.args.get('post_id')  # `post_id` from `postsDetails`

    if not any([title, url, id_, post_id]):
        return jsonify({"error": "Missing title, URL, id, or post_id parameter"}), 400

    # ✅ Search in `posts` collection by `id`, `title`, or `url`
    query = {}
    if id_:
        query["id"] = id_
    elif title and url:
        query = {"title": title, "url": url}
    elif title:
        query = {"title": title}
    elif url:
        query = {"url": url}

    post = collection.find_one(query, {"_id": 0})
    if post:
        return jsonify(post)

    # ✅ Search in `postsDetails` collection by `post_id`
    query = {}
    if post_id:
        query["post_id"] = post_id

    post_details = posts_details_collection.find_one(query, {"_id": 0})
    if post_details:
        return jsonify(post_details)

    return jsonify({"error": "Post not found"}), 404



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
    url = request.args.get('url')  # Get URL from query parameter

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    categories = extract_categories(url)
    return jsonify(categories)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
