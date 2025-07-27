from flask import Flask, jsonify, render_template, request, redirect, session, url_for
from flask_cors import CORS
import requests

app = Flask(__name__, template_folder='frontend', static_folder='static')
CORS(app)

app.secret_key = 'secret_key'


# API_KEY = "2b0ce3059d354a90a61fd21c3defc4cb"
API_KEY = "176cc7bb21a546e8b9144ecec6585834"
BASE_URL = "https://newsapi.org/v2/top-headlines"

# Route for index.html 
@app.route('/')
def home():
    username = session.get('user')
    return render_template('index.html', username=username)

# Fetching News from API's
@app.route('/get-news')
def get_news():
    category = request.args.get('category')  
    params = {
        'apiKey': API_KEY,
        'country': 'us',
        'pageSize': 15
    }
    if category:
        params['category'] = category
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        print("🔎 News fetched:", response.json())
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(" Error:", e)
        return jsonify({'status': 'error', 'message': 'Failed to fetch news'}), 500

# Redirect to article.html file
@app.route('/article')
def article():
    return render_template('article.html')

# login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Dummy check 
        if username == 'aditya' and password == '1234':
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# Redirect to Main Page
@app.route('/Home')
def homepage():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
