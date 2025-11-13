# compare_backend.py
from textblob import TextBlob
import requests

# 🔑 Your API key (use NewsAPI or Mediastack)
NEWS_API_KEY = "48f19530e2564c05854fa4cca506d829"

# 🌍 Source Bias Map
source_bias_map = {
    # 🌐 Global Left-Leaning
    "cnn.com": "left",
    "nytimes.com": "left",
    "theguardian.com": "left",
    "msnbc.com": "left",
    "huffpost.com": "left",
    "vox.com": "left",
    "slate.com": "left",
    "politico.com": "left",
    # 🌐 Global Right-Leaning
    "foxnews.com": "right",
    "breitbart.com": "right",
    "theepochtimes.com": "right",
    "newsmax.com": "right",
    "washingtontimes.com": "right",
    # 🌐 Global Center/Neutral
    "bbc.com": "center",
    "reuters.com": "center",
    "apnews.com": "center",
    "npr.org": "center",
    "aljazeera.com": "center",
    "forbes.com": "center",
    # 🇮🇳 Indian Left-Leaning
    "scroll.in": "left",
    "thewire.in": "left",
    "newslaundry.com": "left",
    "thequint.com": "left",
    "theprint.in": "left",
    "ndtv.com": "left",
    # 🇮🇳 Indian Right-Leaning
    "opindia.com": "right",
    "swarajyamag.com": "right",
    "republicworld.com": "right",
    "zeenews.india.com": "right",
    "timesnownews.com": "right",
    # 🇮🇳 Indian Center/Neutral
    "indiatoday.in": "center",
    "hindustantimes.com": "center",
    "thehindu.com": "center",
    "livemint.com": "center",
    "business-standard.com": "center",
    "economictimes.indiatimes.com": "center",
    "news18.com": "center",
    "toi.com": "center",
    "timesofindia.indiatimes.com": "center",
}

# 🧠 Detect bias based on source URL
def get_source_bias(url):
    for domain in source_bias_map:
        if domain in url:
            return source_bias_map[domain]
    return "unknown"

# 🧠 Detect sentiment polarity of article text
def get_sentiment_bias(text):
    if not text or not isinstance(text, str):
        return "unknown"
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"

# 🧩 Combined bias result
def detect_bias(url, article_text):
    return {
        "source_bias": get_source_bias(url),
        "sentiment_bias": get_sentiment_bias(article_text)
    }

# 📰 NEW FEATURE: Compare similar news across platforms
def fetch_similar_articles(title):
    import re
    import requests
    from textblob import TextBlob

    if not title:
        return []

    # Simplify title into keywords
    title = re.sub(r'[^a-zA-Z0-9 ]', '', title)
    keywords = " ".join(title.split()[:5])  # use top 5 words

    url = f"https://newsapi.org/v2/everything?q={keywords}&language=en&sortBy=relevancy&apiKey={NEWS_API_KEY}"
    print("🔍 Searching for:", keywords)

    try:
        response = requests.get(url)
        data = response.json()

        if data.get("status") != "ok":
            print("⚠️ API Error:", data)
            return []

        articles = []
        for article in data.get("articles", [])[:6]:
            source_url = article.get("url", "")
            content = article.get("description") or article.get("content", "")
            bias_info = detect_bias(source_url, content)

            articles.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "source": article["source"]["name"],
                "bias": bias_info["source_bias"]
            })

        print(f"✅ Found {len(articles)} similar articles.")
        return articles

    except Exception as e:
        print("⚠️ Error fetching comparison articles:", e)
        return []
