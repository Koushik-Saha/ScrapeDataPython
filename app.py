from flask import Flask, request, jsonify
from scraper import scrape_homepage
from scraperDetails import scrape_post_details
from scraperCategoryList import scrape_category_posts
from scraperCategoryListName import extract_categories

app = Flask(__name__)

@app.route('/scrape-homepage', methods=['GET'])
def scrape_home():
    """API endpoint to get paginated posts."""
    page = request.args.get('page', default=1, type=int)  # Default: Page 1
    limit = request.args.get('limit', default=15, type=int)  # Default: 15 posts

    # Validate limit (max 15)
    if limit > 15:
        return jsonify({"error": "Limit cannot be greater than 15"}), 400

    data = scrape_homepage(page=page, limit=limit)
    return jsonify(data)


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