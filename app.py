from bson.json_util import dumps

from flask import Flask, request, jsonify
from pymongo.errors import DuplicateKeyError

from scraper import scrape_homepage
from scraperDetails import scrape_post_details
from scraperCategoryList import scrape_category_posts
from scraperCategoryListName import extract_categories
from pymongo import MongoClient
from bson import ObjectId  # ✅ Import BSON for ObjectId

app = Flask(__name__)

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


@app.route('/scrape-post', methods=['GET'])
def scrape_post_api():
    """API endpoint to get post details from a given URL."""
    url = request.args.get('url')

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    # ✅ Check if the post already exists before inserting
    existing_post = posts_details_collection.find_one({"url": url}, {"_id": 0})

    if existing_post:
        return jsonify({"message": "Post already exists",
                        "data": existing_post}), 200  # ✅ Return existing post instead of inserting

    post_data = scrape_post_details(url)

    # Ensure post_data contains a valid URL
    if "url" not in post_data or not post_data["url"]:
        return jsonify({"error": "Scraped data does not contain a valid URL"}), 400

    try:
        inserted_post = posts_details_collection.insert_one(post_data)
        post_data["_id"] = str(inserted_post.inserted_id)  # ✅ Convert ObjectId to string
        return dumps(post_data)  # ✅ Handles ObjectId serialization
    except DuplicateKeyError:
        return jsonify({"error": "Duplicate entry detected"}), 400

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