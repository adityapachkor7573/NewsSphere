import requests
from bs4 import BeautifulSoup

def scrape_full_article(url):
    """
    Scrape the main content + images from a news article URL.
    Returns: dict with title, paragraphs, and image list.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Title
        title = soup.title.string if soup.title else "Untitled Article"

        # Paragraphs (try common article containers)
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text and len(text.split()) > 5:  # skip very short lines
                paragraphs.append(text)

        # Images (absolute URLs only)
        images = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and src.startswith("http"):
                images.append(src)

        return {
            "title": title,
            "content": paragraphs,
            "images": images
        }

    except Exception as e:
        return {
            "title": "Error loading article",
            "content": [f"⚠️ Error while scraping: {str(e)}"],
            "images": []
        }
