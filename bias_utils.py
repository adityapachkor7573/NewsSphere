# bias_utils.py

from textblob import TextBlob

# Predefined source bias labels
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


def get_source_bias(url):
    for domain in source_bias_map:
        if domain in url:
            return source_bias_map[domain]
    return "unknown"

# --- bias_utils.py ---

def get_sentiment_bias(text):
    # ✅ Prevent crash if text is None or empty
    if not text or not isinstance(text, str):
        return "unknown"  # fallback label
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"


def detect_bias(url, article_text):
    return {
        "source_bias": get_source_bias(url),
        "sentiment_bias": get_sentiment_bias(article_text)
    }
