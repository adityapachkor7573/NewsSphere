from flask import Flask, jsonify, render_template, request, redirect, session, url_for
from flask_cors import CORS
import requests
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__, template_folder='frontend', static_folder='static')
CORS(app)
app.secret_key = 'your_secret_key'

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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

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
@app.route('/admin-login', methods=['GET', 'POST'])
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
    return render_template('view-users.html', users=users)


# --- News Fetching Routes ---
@app.route('/get-news')
def get_news():
    category = request.args.get('category')
    params = {'apiKey': NEWS_API_KEY, 'country': 'us', 'pageSize': 15}
    if category:
        params['category'] = category
    try:
        response = requests.get(NEWS_BASE_URL, params=params)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print("❌ NewsAPI Error:", e)
        return jsonify({'status': 'error', 'message': 'Failed to fetch news'}), 500

# --- Featching news for India ---
# --- For  Featching Indian News data form MEDIASTACK ---
@app.route('/get-india-news')
def get_india_news():
    category = request.args.get('category')
    combined_articles = []

    # Mediastack
    mediastack_params = {
        'access_key': MEDIASTACK_API_KEY,
        'countries': 'in',
        'limit': 10,
        'languages': 'en',
        'sort': 'published_desc'
    }
    if category and category != 'india':
        mediastack_params['categories'] = category

    try:
        res1 = requests.get(MEDIASTACK_BASE_URL, params=mediastack_params)
        res1.raise_for_status()
        data1 = res1.json().get('data', [])
        for article in data1:
            combined_articles.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'content': article.get('description'),
                'url': article.get('url'),
                'urlToImage': article.get('image'),
                'publishedAt': article.get('published_at'),
                'source': {'name': article.get('source')}
            })
    except Exception as e:
        print("❌ Mediastack India Error:", e)

    # NewsAPI
    newsapi_params = {
        'apiKey': NEWS_API_KEY,
        'country': 'in',
        'pageSize': 10
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
                'source': {'name': article.get('source', {}).get('name')}
            })
    except Exception as e:
        print("❌ NewsAPI India Error:", e)

    return jsonify({'articles': combined_articles})

# --- Featching news for World ---
@app.route('/get-world-news')
def get_world_news():
    combined_articles = []

    # NewsAPI
    newsapi_params = {
        'apiKey': NEWS_API_KEY,
        'category': 'general',
        'pageSize': 10,
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
                'source': {'name': article.get('source', {}).get('name')}
            })
    except requests.exceptions.RequestException as e:
        print("❌ NewsAPI World Error:", e)

    # Mediastack
    mediastack_params = {
        'access_key': MEDIASTACK_API_KEY,
        'countries': 'us,gb,au,ca',
        'languages': 'en',
        'limit': 10,
        'sort': 'published_desc'
    }
    try:
        response = requests.get(MEDIASTACK_BASE_URL, params=mediastack_params)
        response.raise_for_status()
        mediastack_data = response.json().get('data', [])
        for article in mediastack_data:
            combined_articles.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'content': article.get('description'),
                'url': article.get('url'),
                'urlToImage': article.get('image'),
                'publishedAt': article.get('published_at'),
                'source': {'name': article.get('source')}
            })
    except requests.exceptions.RequestException as e:
        print("❌ Mediastack World Error:", e)

    return jsonify({'articles': combined_articles})


# --- Initialize DB ---
init_db()

if __name__ == '__main__':
    app.run(debug=True)