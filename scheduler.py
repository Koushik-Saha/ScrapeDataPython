import schedule
import time
import requests
from pymongo import MongoClient

# ✅ Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["scraped_data"]
collection = db["posts"]

# ✅ Configuration
BASE_URL = "http://127.0.0.1:5000/scrape-homepage"
LIMIT = 15
MAX_PAGES = 723  # Change this based on how many pages you want to scrape
current_page = 408  # Start from page 1

def scrape_and_store():
    """Scrapes data from API and stores in MongoDB every 5 seconds."""
    global current_page

    if current_page > MAX_PAGES:
        print("✅ All pages have been scraped. Stopping the script! 🚀")
        schedule.clear()  # Stop the scheduler
        return

    url = f"{BASE_URL}?page={current_page}&limit={LIMIT}"
    print(f"🔄 Scraping Page {current_page}: {url}")

    try:
        response = requests.get(url)
        data = response.json()

        if "posts" in data and len(data["posts"]) > 0:
            # ✅ Store in MongoDB (Avoid duplicates)
            for post in data["posts"]:
                if not collection.find_one({"url": post["url"]}):  # Check if already exists
                    collection.insert_one(post)

            print(f"✅ Stored {len(data['posts'])} posts from page {current_page} in MongoDB!")
        else:
            print(f"⚠️ No posts found on page {current_page}")

    except Exception as e:
        print(f"❌ Error scraping page {current_page}: {e}")

    # ✅ Move to the next page
    current_page += 1

# ✅ Schedule API call every 5 seconds
schedule.every(5).seconds.do(scrape_and_store)

print("🚀 Auto-scraping started! Calling API every 5 seconds...")

while schedule.jobs:
    schedule.run_pending()
    time.sleep(1)  # Prevent excessive CPU usage

print("✅ Script has stopped successfully! 🎉")