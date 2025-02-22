import uuid
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pymongo import MongoClient

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["scraped_data"]
    posts_collection = db["posts"]
    posts_details_collection = db["postsDetails"]
    logging.info("✅ Connected to MongoDB successfully!")
except Exception as e:
    logging.error(f"❌ MongoDB Connection Error: {e}")

# ✅ Set up ChromeDriver
CHROME_DRIVER_PATH = ChromeDriverManager().install()
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")


def scrape_post_details(post_url):
    """Scrapes post details and saves in MongoDB with reference to `posts` collection."""

    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    driver.get(post_url)
    time.sleep(5)  # Allow JavaScript to load
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # ✅ Retrieve `_id` from `posts` collection
    post = posts_collection.find_one({"url": post_url}, {"id": 1})  # ✅ Use `_id`, not `id`

    if not post:
        logging.warning(f"⚠️ Post not found in 'posts' collection: {post_url}")
        return {"error": "Post not found in 'posts' collection"}

    posts_collection_id = str(post["id"])  # ✅ Use `_id` safely

    if posts_details_collection.find_one({"post_collection_id": posts_collection_id}):
        logging.info(f"⚠️ Post details already exist for post_collection_id: {posts_collection_id}")
        return {"success": True, "message": "Post details already exist", "post_collection_id": posts_collection_id}


    # Generate a unique post_id
    post_id = str(uuid.uuid4())

    # Scrape the page...
    url = post_url  # Ensure this value is always set

    # Extract Title
    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "No Title Found"

    # Extract Author
    author_tag = soup.find("span", class_="author")
    author = author_tag.text.strip() if author_tag else "No Author Found"

    # Extract Date
    date_tag = soup.find("time")
    date = date_tag.text.strip() if date_tag else "No Date Found"

    # Extract Views
    views_tag = soup.find("span", class_="post-views-eye")
    views = views_tag.text.strip() if views_tag else "No Views Found"

    # ✅ Extract All Paragraphs Inside `entry-content` Div
    content_div = soup.find("div", class_="entry-content")
    subtitle = " ".join([p.text.strip() + "।" for p in content_div.find_all("p")]) if content_div else "No Content Found"

    # Extract Category
    category_tag = soup.find("a", rel="category tag")
    category = category_tag.text.strip() if category_tag else "No Category Found"

    # Extract Tags
    tags = [tag.text.strip() for tag in soup.find_all("a", rel="tag")]

    # ✅ Extract Previous Post
    previous_post_div = soup.find("div", class_="nav-previous")
    previous_post = {
        "name": previous_post_div.find("a", rel="prev").text.strip(),
        "url": previous_post_div.find("a", rel="prev")["href"]
    } if previous_post_div and previous_post_div.find("a", rel="prev") else {"name": "No Previous Post Found", "url": ""}

    # ✅ Extract Suggested Posts
    suggested_posts_divs = soup.find_all("section", class_="related-stories")
    suggested_posts = [
        {"name": a.text.strip(), "url": a["href"]}
        for a in (suggested_posts_divs[1].find_all("a", rel="bookmark") if len(suggested_posts_divs) > 1 else [])
    ]

    # ✅ Structure Data for MongoDB
    post_data = {
        "post_id": post_id,  # ✅ Connects with `id` in `posts`
        "post_collection_id": posts_collection_id,
        "url": url,
        "title": title,
        "author": author,
        "date": date,
        "views": views,
        "subtitle": subtitle,
        "category": category,
        "tags": tags,
        "previous_post": previous_post,
        "suggested_posts": suggested_posts
    }

    # ✅ Save to MongoDB
    try:
        result = posts_details_collection.insert_one(post_data)
        logging.info(f"✅ Data inserted successfully with ID: {result.inserted_id}")
        return {"success": True, "message": "Data inserted successfully", "post_id": str(result.inserted_id)}
    except Exception as e:
        logging.error(f"❌ MongoDB Insert Error: {e}")
        return {"error": f"Database insert error: {str(e)}"}


if __name__ == "__main__":
    post_url = "https://www.banglachotikahinii.com/best-bangla-choti/amar-sunori-bouma-arunima-8/"
    post_data = scrape_post_details(post_url)
    print(post_data)