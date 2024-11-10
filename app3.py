from flask import Flask, request, redirect, render_template, url_for, flash, session, send_from_directory, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS
import bcrypt

app = Flask(__name__)
app.secret_key = '522cf0143346652762d42387e84abe7a'  # Replace with a secure key

# Enable CORS for frontend requests from specific origins
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['trading_tracker_db']
users_collection = db['users']
entries_collection = db['entries']  # New collection for storing user-specific entries

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
            return redirect(f"http://localhost:3000/set-session?user={user['contact']}")
        else:
            flash('Invalid login credentials!')
            return redirect(url_for('login_page'))
    
    return render_template('login.html')

# Route to render the login page
@app.route('/')
def login_page():
    if 'user' in session:  # If already logged in, redirect to index
        return redirect(url_for('index'))
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

# Route for user-specific entries with GET, POST, PUT, DELETE functionality
@app.route('/api/entries', methods=['GET', 'POST'])
def user_entries():
    if 'user' not in session:
        flash('You need to log in first!')
        return redirect(url_for('login_page'))

    user_contact = session['user']
    
    if request.method == 'GET':
        # Fetch user-specific entries from MongoDB
        entries = list(entries_collection.find({'user_contact': user_contact}, {'_id': False}))
        return jsonify(entries=entries)

    if request.method == 'POST':
        # Add new entry for the user
        new_entry = request.json
        new_entry['user_contact'] = user_contact  # Associate entry with logged-in user
        entries_collection.insert_one(new_entry)
        return jsonify({'message': 'Entry added successfully'}), 201

# Route to update an entry
@app.route('/api/entries/<entry_id>', methods=['PUT'])
def update_entry(entry_id):
    if 'user' not in session:
        flash('You need to log in first!')
        return redirect(url_for('login_page'))

    user_contact = session['user']
    updated_data = request.json

    result = entries_collection.update_one(
        {'_id': ObjectId(entry_id), 'user_contact': user_contact},
        {'$set': updated_data}
    )

    if result.matched_count == 0:
        return jsonify({'message': 'Entry not found or not authorized'}), 404
    return jsonify({'message': 'Entry updated successfully'})

# Route to delete an entry
@app.route('/api/entries/<entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    if 'user' not in session:
        flash('You need to log in first!')
        return redirect(url_for('login_page'))

    user_contact = session['user']
    result = entries_collection.delete_one({'_id': ObjectId(entry_id), 'user_contact': user_contact})

    if result.deleted_count == 0:
        return jsonify({'message': 'Entry not found or not authorized'}), 404
    return jsonify({'message': 'Entry deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)
