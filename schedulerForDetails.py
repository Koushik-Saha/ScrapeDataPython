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
    all_posts = list(posts_collection.find({}, {"url": 1, "_id": 0, "id": 1}))
    post_count = 0  # Counter for saved posts
    skipped_count = 0  # Counter for skipped posts

    if not all_posts:
        print("✅ No posts found in the database. Exiting...")
        schedule.clear()
        return

    for post in all_posts:
        post_url = post.get("url")
        post_id = post.get("id")

        if not post_url or not post_id:
            print("⚠️ Skipping post with missing URL or post ID")
            skipped_count += 1
            continue

        # ✅ Check if already exists in `postsDetails`
        if posts_details_collection.find_one({"post_collection_id": post_id}):
            print(f"⚠️ Post already exists in postsDetails, skipping: {post_id}")
            skipped_count += 1
            continue  # Move to the next post

        print(f"🔄 Scraping post: {post_url} && postId: {post_id}")

        try:
            response = requests.get(f"{SCRAPE_API}?url={post_url}")

            # 🚀 Debugging API Response
            print(f"🔍 Response Status: {response.status_code}")
            print(f"📜 Response Headers: {response.headers}")

            if response.status_code in [200, 201]:  # ✅ Handle both success cases
                post_data = response.json()
                print(f"📊 Scraped Data: {post_data}")

                if "data" in post_data and "post_id" in post_data["data"]:
                    inserted = posts_details_collection.insert_one(post_data)
                    post_count += 1  # Increment counter
                    print(f"✅ Post {post_count} saved with ID: {inserted.inserted_id}")
                else:
                    print(f"⚠️ Scraped data does not contain a valid URL: {post_url}")

            elif response.status_code == 500:
                print(f"❌ API request failed with 500 INTERNAL SERVER ERROR for {post_url}")
                print(f"🛑 Error Message: {response.text}")  # ✅ Print full error message from the API

            else:
                print(f"❌ API request failed for {post_url}, Status Code: {response.status_code}, Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"🚨 Network Error: {e}")  # ✅ Print network-related errors
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")  # ✅ Catch unexpected Python errors

    # ✅ Check if all posts are processed
    total_posts = len(all_posts)
    if post_count + skipped_count >= total_posts:
        print(f"🎉 All {total_posts} posts have been processed! Stopping the script.")
        schedule.clear()

# ✅ Schedule the script to run every 1 second
schedule.every(1).seconds.do(scrape_and_store)

print("🚀 Auto-scraping started! Calling API every 1 second...")

while schedule.jobs:
    schedule.run_pending()
    time.sleep(1)  # Prevent excessive CPU usage

print("✅ Scraping process completed. Exiting script.")