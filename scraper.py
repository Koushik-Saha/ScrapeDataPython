from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def scrape_homepage(page=1, limit=15):
    """Scrapes posts from the homepage with pagination and limit."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Construct the paginated URL
    homepage_url = f"https://www.banglachotikahinii.com/page/{page}/"
    driver.get(homepage_url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Find all post articles
    posts = soup.find_all("article")

    post_details = []

    for post in posts[:limit]:  # Ensure we don't exceed the limit
        # ✅ Extract Post Title and URL
        title_tag = post.find("h2", class_="entry-title")
        if title_tag:
            title_link = title_tag.find("a")
            title = title_link.text.strip() if title_link else "No Title Found"
            post_url = title_link["href"] if title_link else "No URL Found"
        else:
            title = "No Title Found"
            post_url = "No URL Found"

        # ✅ Extract Author
        author_tag = post.find("span", class_="author-name")
        author = author_tag.text.strip() if author_tag else "No Author Found"

        # ✅ Extract Date
        date_tag = post.find("time", class_="entry-date")
        date = date_tag.text.strip() if date_tag else "No Date Found"

        # ✅ Extract Views
        views_tag = post.find("span", class_="post-views-eye")
        views = views_tag.text.strip() if views_tag else "No Views Found"

        # ✅ Extract Subtitle (First Paragraph)
        subtitle_tag = post.find("p")
        subtitle = subtitle_tag.text.strip() if subtitle_tag else "No Subtitle Found"

        # ✅ Extract Category
        category_tag = post.find("a", rel="category tag")
        category = category_tag.text.strip() if category_tag else "No Category Found"

        # ✅ Extract Tags
        tags = [tag.text.strip() for tag in post.find_all("a", rel="tag")]

        post_details.append({
            "title": title,
            "url": post_url,  # ✅ Now includes URL
            "author": author,
            "date": date,
            "views": views,
            "subtitle": subtitle,
            "category": category,
            "tags": tags
        })

    return {
        "page": page,
        "limit": limit,
        "total_posts": len(post_details),
        "posts": post_details
    }

if __name__ == "__main__":
    scraped_data = scrape_homepage(page=1, limit=15)
    print(scraped_data)