import uuid

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pymongo import MongoClient
import time
import logging

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["scraped_data"]  # Database name
    collection = db["postsDetails"]  # Collection name
    logging.info("✅ Connected to MongoDB successfully!")
except Exception as e:
    logging.error(f"❌ MongoDB Connection Error: {e}")

# ✅ Set up ChromeDriver once (so it doesn’t download every time)
CHROME_DRIVER_PATH = ChromeDriverManager().install()


def scrape_post_details(post_url):
    """Scrapes all content from a post dynamically and saves it in MongoDB."""

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Load the post URL
    driver.get(post_url)
    time.sleep(5)  # Allow JavaScript to load

    # Parse the fully loaded page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Generate a unique post_id
    post_id = str(uuid.uuid4())

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
    if content_div:
        paragraphs = [p.text.strip() + "।" for p in content_div.find_all("p")]  # Add '।' after each paragraph
        subtitle = " ".join(paragraphs)  # Join all paragraphs into one text
    else:
        subtitle = "No Content Found"

    # Extract Category
    category_tag = soup.find("a", rel="category tag")
    category = category_tag.text.strip() if category_tag else "No Category Found"

    # Extract Tags
    tags = [tag.text.strip() for tag in soup.find_all("a", rel="tag")]

    # ✅ Extract Correct Previous Post Title with URL
    previous_post_div = soup.find("div", class_="nav-previous")
    if previous_post_div:
        previous_post_tag = previous_post_div.find("a", rel="prev")  # Get <a> inside nav-previous
        previous_post = {
            "name": previous_post_tag.text.strip(),
            "url": previous_post_tag["href"]
        } if previous_post_tag else {"name": "No Previous Post Found", "url": ""}
    else:
        previous_post = {"name": "No Previous Post Found", "url": ""}

    # ✅ Extract the Second `related-stories` Section
    suggested_posts_divs = soup.find_all("section", class_="related-stories")
    if len(suggested_posts_divs) > 1:  # Ensure there are at least two sections
        suggested_posts_div = suggested_posts_divs[1]  # Select the second one
    else:
        suggested_posts_div = None

    # ✅ Extract Suggested Posts with URLs
    suggested_posts = []
    if suggested_posts_div:
        for a in suggested_posts_div.find_all("a", rel="bookmark"):
            suggested_posts.append({
                "name": a.text.strip(),
                "url": a["href"]
            })

    # ✅ Structure Data for MongoDB
    post_data = {
        "post_id": post_id,  # ✅ Connects with `id` in `posts`
        "title": title,
        "author": author,
        "date": date,
        "views": views,
        "subtitle": subtitle,  # ✅ Now contains all paragraphs
        "category": category,
        "tags": tags,
        "previous_post": previous_post,  # ✅ Now contains both name & URL
        "suggested_posts": suggested_posts  # ✅ Now correctly selects the second related-stories section
    }

    # ✅ Save to MongoDB
    try:
        result = collection.insert_one(post_data)
        logging.info(f"✅ Data inserted successfully with ID: {result.inserted_id}")
    except Exception as e:
        logging.error(f"❌ MongoDB Insert Error: {e}")

    return post_data


if __name__ == "__main__":
    post_url = "https://www.banglachotikahinii.com/best-bangla-choti/amar-sunori-bouma-arunima-8/"
    post_data = scrape_post_details(post_url)
    print(post_data)