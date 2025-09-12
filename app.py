from flask import Flask, jsonify, render_template, request, redirect, session, url_for
from flask_cors import CORS
import requests
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
from bias_utils import detect_bias
from admin_routes import admin_bp 
from activity_routes import activity_bp

app = Flask(__name__, template_folder='frontend', static_folder='static')
CORS(app)
app.secret_key = '4af8976b03edce09f3331af4859305d3b219ae1dd36a4f8f'

# --- Configuration ---
NEWS_API_KEY = "176cc7bb21a546e8b9144ecec6585834"
NEWS_BASE_URL = "https://newsapi.org/v2/top-headlines"
MEDIASTACK_API_KEY = "3f070ed070e4bc5eb2bf4fdc4ef25d39"
MEDIASTACK_BASE_URL = "http://api.mediastack.com/v1/news"
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'adityapachkor90@gmail.com'
EMAIL_PASSWORD = 'odre anaz ctqk txhc'
DB_PATH = 'users.db'

app.register_blueprint(admin_bp)
app.register_blueprint(activity_bp)

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()


# --- Email OTP Function ---
def send_otp_email(recipient, otp):
    try:
        message = MIMEText(f"Your OTP is: {otp}")
        message['Subject'] = "Your OTP Verification Code"
        message['From'] = EMAIL_ADDRESS
        message['To'] = recipient
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False


# ✅ Helper to ensure minimum 50 articles
def ensure_min_articles(articles, fallback_params, min_count=50):
    if len(articles) < min_count:
        try:
            res2 = requests.get(MEDIASTACK_BASE_URL, params=fallback_params)
            res2.raise_for_status()
            data2 = res2.json().get('data', [])
            for article in data2:
                articles.append({
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'content': article.get('description'),
                    'url': article.get('url'),
                    'urlToImage': article.get('image'),
                    'publishedAt': article.get('published_at'),
                    'source': {'name': article.get('source')},
                    'bias': detect_bias(article.get('url'), article.get('description', ''))
                })
                if len(articles) >= min_count:
                    break
        except Exception as e:
            print("⚠️ Fallback Mediastack error:", e)
    return articles[:100]


# --- Routes ---
@app.route('/')
def home():
    username = session.get('user')
    return render_template('index.html', username=username)


# --- Register Page ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        otp = str(random.randint(100000, 999999))
        session['temp_user'] = {'username': username, 'password': password, 'email': email, 'otp': otp}
        if send_otp_email(email, otp):
            return redirect(url_for('verify_otp'))
        else:
            return render_template('register.html', error="Failed to send OTP.")
    return render_template('register.html')


# --- Verification OTP ---
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp_entered = request.form['otp']
        temp = session.get('temp_user')
        if temp and temp['otp'] == otp_entered:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                          (temp['username'], temp['password'], temp['email']))
                conn.commit()
                conn.close()
                session.pop('temp_user')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                return render_template('verify_otp.html', error="User already exists.")
        return render_template('verify_otp.html', error="Invalid OTP.")
    return render_template('verify_otp.html')


# --- Login Page ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next') or request.form.get('next') or url_for('home')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = username
            session['user_id'] = user[0]

            from activity_routes import log_activity
            log_activity(user_id=user[0], activity_type='login')

            return redirect(next_page)
        else:
            return render_template('login.html', error="Invalid credentials", next=next_page)

    return render_template('login.html', next=next_page)


# --- User Logout ---
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))


# --- Article Page ---
@app.route('/article')
def article():
    return render_template('article.html')


# --- Admin Login ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')


# --- Admin Dashboard --- 
@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, email FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', users=users)


# --- News Fetching Routes ---
@app.route('/get-news')
def get_news():
    category = request.args.get('category')
    params = {'apiKey': NEWS_API_KEY, 'country': 'us', 'pageSize': 100}
    if category:
        params['category'] = category
    try:
        response = requests.get(NEWS_BASE_URL, params=params)
        response.raise_for_status()
        articles = response.json().get('articles', [])

        fallback_params = {
            'access_key': MEDIASTACK_API_KEY,
            'countries': 'us',
            'languages': 'en',
            'limit': 100,
            'sort': 'published_desc'
        }
        articles = ensure_min_articles(articles, fallback_params)
        return jsonify({'articles': articles})
    except requests.exceptions.RequestException as e:
        print("❌ NewsAPI Error:", e)
        return jsonify({'status': 'error', 'message': 'Failed to fetch news'}), 500


# --- Featching news for India ---
@app.route('/get-india-news')
def get_india_news():
    category = request.args.get('category')
    combined_articles = []

    newsapi_params = {
        'apiKey': NEWS_API_KEY,
        'country': 'in',
        'pageSize': 100
    }
    if category and category != 'india':
        newsapi_params['category'] = category

    try:
        res2 = requests.get(NEWS_BASE_URL, params=newsapi_params)
        res2.raise_for_status()
        data2 = res2.json().get('articles', [])
        for article in data2:
            combined_articles.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'content': article.get('content'),
                'url': article.get('url'),
                'urlToImage': article.get('urlToImage'),
                'publishedAt': article.get('publishedAt'),
                'source': {'name': article.get('source', {}).get('name')},
                'bias': detect_bias(article.get('url'), article.get('description', ''))
            })
    except Exception as e:
        print("❌ NewsAPI India Error:", e)

    fallback_params = {
        'access_key': MEDIASTACK_API_KEY,
        'countries': 'in',
        'languages': 'en',
        'limit': 100,
        'sort': 'published_desc'
    }
    combined_articles = ensure_min_articles(combined_articles, fallback_params)
    return jsonify({'articles': combined_articles})


# --- Featching news for World ---
@app.route('/get-world-news')
def get_world_news():
    combined_articles = []

    newsapi_params = {
        'apiKey': NEWS_API_KEY,
        'category': 'general',
        'pageSize': 100,
        'language': 'en'
    }
    try:
        response = requests.get(NEWS_BASE_URL, params=newsapi_params)
        response.raise_for_status()
        newsapi_data = response.json().get('articles', [])
        for article in newsapi_data:
            combined_articles.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'content': article.get('content'),
                'url': article.get('url'),
                'urlToImage': article.get('urlToImage'),
                'publishedAt': article.get('publishedAt'),
                'source': {'name': article.get('source', {}).get('name')},
                'bias': detect_bias(article.get('url'), article.get('description', ''))
            })
    except requests.exceptions.RequestException as e:
        print("❌ NewsAPI World Error:", e)

    fallback_params = {
        'access_key': MEDIASTACK_API_KEY,
        'countries': 'us,gb,au,ca',
        'languages': 'en',
        'limit': 100,
        'sort': 'published_desc'
    }
    combined_articles = ensure_min_articles(combined_articles, fallback_params)
    return jsonify({'articles': combined_articles})


# --- Featching news for search ---
@app.route("/search-news")
def search_news():
    query = request.args.get("query", "")
    if not query:
        return jsonify({"articles": []})

    url = f"https://newsapi.org/v2/everything?q={query}&language=en&pageSize=100&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get("articles", [])

        fallback_params = {
            'access_key': MEDIASTACK_API_KEY,
            'keywords': query,
            'languages': 'en',
            'limit': 100,
            'sort': 'published_desc'
        }
        articles = ensure_min_articles(articles, fallback_params)
        return jsonify({"articles": articles})
    except Exception as e:
        print("Error fetching search results:", e)
        return jsonify({"articles": []})




# --- Initialize DB ---
init_db()

if __name__ == '__main__':
    app.run(debug=True)
