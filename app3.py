from flask import Flask, request, redirect, render_template, url_for, flash, session, send_from_directory
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
app.secret_key = '522cf0143346652762d42387e84abe7a'  # Replace with a secure key

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['trading_tracker_db']
users_collection = db['users']

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Route for signup (creating a new user)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        password = request.form['password']

        # Check if user already exists
        if users_collection.find_one({'contact': contact}):
            flash('User already exists!')
            return redirect(url_for('signup'))

        # Hash the password and store it in MongoDB
        hashed_password = hash_password(password)
        users_collection.insert_one({
            'name': name,
            'contact': contact,
            'password': hashed_password
        })
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login_page'))
    
    return render_template('signup.html')

# Route for login (validating a user)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        contact = request.form['contact']
        password = request.form['password']
        
        # Find the user in MongoDB
        user = users_collection.find_one({'contact': contact})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user'] = user['contact']  # Set session with the user's contact
            flash("Login successful!")
            return redirect("http://localhost:3000/set-session")  # Redirect to Node.js to set session
        else:
            flash('Invalid login credentials!')
            return redirect(url_for('login_page'))
    
    return render_template('login.html')

# Route to render the login page
@app.route('/')
def login_page():
    return render_template('login.html')

# Main page after successful login, serves index.html from public directory
@app.route('/index')
def index():
    if 'user' not in session:  # Check if user is in the session
        flash('You need to log in first!')
        return redirect(url_for('login_page'))
    return send_from_directory('public', 'index.html')  # Serve static index.html from public

# Route to log out the user
@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove user from session
    flash('You have been logged out.')
    return redirect("http://localhost:3000/logout")  # Redirect to Node.js logout route

if __name__ == '__main__':
    app.run(debug=True)
