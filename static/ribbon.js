function updateLatestNews(articles) {
  const latestNewsSpan = document.getElementById("latest-news-text");
  if (!articles || articles.length === 0) {
    latestNewsSpan.innerText = "No latest news available.";
    return;
  }

  const headlines = articles.slice(0, 10).map(a => a.title).join(" | | ");
  latestNewsSpan.innerText = headlines;
}

fetch('/get-news?category=general')
  .then(res => res.json())
  .then(data => {
    const articles = data.articles || data.data || [];
    updateLatestNews(articles);
  })
  .catch(err => {
    console.error("Error fetching latest news for ribbon:", err);
    document.getElementById("latest-news-text").innerText = "Error loading latest news.";
  });