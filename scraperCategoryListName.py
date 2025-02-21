from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


def extract_categories(post_url):
    """Scrapes all content from a post dynamically."""

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
    categories = []

    # Find all category items
    category_list = soup.select(".wp-block-categories-list li")

    for category in category_list:
        link = category.find("a")
        if link:
            name = link.text.strip()
            url = link["href"]
            count = category.text.replace(name, "").strip()
            count = int(count.replace("(", "").replace(")", "").replace(",", "").strip()) if count else 0

            categories.append({
                "name": name,
                "url": url,
                "count": count
            })

    return categories


if __name__ == "__main__":
    post_url = "https://www.banglachotikahinii.com/"
    post_data = extract_categories(post_url)
    print(post_data)