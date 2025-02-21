from flask import Flask, request, jsonify
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
    url = request.args.get('url')  # Get URL from query parameter

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    post_data = scrape_post_details(url)
    return jsonify(post_data)

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