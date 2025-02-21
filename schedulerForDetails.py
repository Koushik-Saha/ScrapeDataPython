import schedule
import time
import requests
from pymongo import MongoClient

# ✅ Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["scraped_data"]
posts_collection = db["posts"]
posts_details_collection = db["postsDetails"]

# ✅ Configuration
SCRAPE_API = "http://127.0.0.1:5000/scrape-post"  # Replace with your actual API endpoint


def scrape_and_store():
    """Fetches posts from 'posts' collection and scrapes only new ones."""

    all_posts = posts_collection.find({}, {"url": 1, "_id": 0})
    post_count = 0  # Counter for saved posts

    for post in all_posts:
        post_url = post.get("url")

        if not post_url:
            print("⚠️ Skipping post with missing URL")
            continue

        if posts_details_collection.find_one({"url": post_url}):
            print(f"⚠️ Post already exists in postsDetails, skipping: {post_url}")
            continue  # Move to the next post

        print(f"🔄 Scraping post: {post_url}")

        try:
            response = requests.get(f"{SCRAPE_API}?url={post_url}")
            if response.status_code == 200:
                post_data = response.json()

                if "url" in post_data:
                    inserted = posts_details_collection.insert_one(post_data)
                    post_count += 1  # Increment counter
                    print(f"✅ Post {post_count} saved with ID: {inserted.inserted_id}")
                else:
                    print(f"⚠️ Scraped data does not contain a valid URL: {post_url}")

            else:
                print(f"❌ API request failed for {post_url}, Status Code: {response.status_code}")

        except Exception as e:
            print(f"❌ Error scraping {post_url}: {e}")

    print(f"🚀 Completed scraping cycle! Total new posts saved: {post_count}")


# ✅ Schedule the script to run every 30 seconds
schedule.every(10).seconds.do(scrape_and_store)

print("🚀 Auto-scraping started! Calling API every 10 seconds...")

while True:
    schedule.run_pending()
    time.sleep(1)  # Prevent excessive CPU usage