"""
Authentication Backend API - Flask Application

This Flask application serves as the backend for the authentication system, providing
endpoints for user login, registration, Google OAuth integration, and user management.
"""

# Standard library imports
import os
from urllib.parse import urlencode

# Third-party imports
import pymongo
from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from passlib.hash import bcrypt
from requests_oauthlib import OAuth2Session

# Application initialization
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "YOUR_FLASK_SECRET_KEY")  # Better to use environment variable
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow HTTP for local testing only
CORS(app, supports_credentials=True)

###############################################################################
# Database Configuration
###############################################################################
mongo_client = pymongo.MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))
db = mongo_client["login_database"]
users_collection = db["users"]

###############################################################################
# Security Configuration
###############################################################################
# In-memory tracking for brute force prevention
failed_login_attempts = {}  # Maps identifiers to attempt counts
LOCKOUT_THRESHOLD = 5      # Number of failures before lockout

# OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID", 
    "133456352418-o6fjcn4sjk06opgma3129ged0ajfvk27.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = os.environ.get(
    "GOOGLE_CLIENT_SECRET", 
    "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"
)
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI", 
    "http://localhost:5000/api/auth/google/callback"
)
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

###############################################################################
# Authentication Routes
###############################################################################
@app.route('/api/login', methods=['POST'])
def login():
    """
    Standard login endpoint that accepts email/phone and password
    
    Validates credentials, tracks failed attempts, and manages session
    """
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')
    
    # Validate required fields
    if not identifier or not password:
        return jsonify({"success": False, "message": "Email/Phone and Password are required"}), 200
        
    # Validate input length
    if len(identifier) > 255:
        return jsonify({"success": False, "message": "Identifier too long"}), 200
        
    if len(password) > 1000:
        return jsonify({"success": False, "message": "Password too long"}), 200
    
    # Find user by email or phone
    user = users_collection.find_one({
        "$or": [
            {"email": identifier},
            {"phone": identifier}
        ]
    })

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 200

    # Check if user is locked out due to too many attempts
    if failed_login_attempts.get(identifier, 0) >= LOCKOUT_THRESHOLD:
        return jsonify({"success": False, "message": "Too many failed attempts"}), 200

    # Verify password
    if user["password"] and bcrypt.verify(password, user["password"]):
        # Reset attempts on success
        failed_login_attempts[identifier] = 0

        # Set session data
        session['logged_in'] = True
        session['user'] = identifier
        return jsonify({"success": True, "message": "Login successful"}), 200
    else:
        # Increment failed attempt counter
        current_attempts = failed_login_attempts.get(identifier, 0) + 1
        failed_login_attempts[identifier] = current_attempts

        if current_attempts >= LOCKOUT_THRESHOLD:
            return jsonify({"success": False, "message": "Too many failed attempts"}), 200
        else:
            return jsonify({"success": False, "message": "Invalid password"}), 200

@app.route('/api/register', methods=['POST'])
def register():
    """
    User registration endpoint
    
    Creates a new user with email/phone and password
    """
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"success": False, "message": "Invalid JSON payload."}), 400

        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")

        # Validate: user must supply a password and either email OR phone.
        if not password or (not email and not phone):
            return jsonify({"success": False, "message": "Email or phone and password are required."}), 400

        # Check if user already exists
        query = {}
        if email:
            query["email"] = email
        if phone:
            query["phone"] = phone

        if users_collection.find_one(query):
            return jsonify({"success": False, "message": "User already exists."}), 400

        # Create new user with hashed password
        hashed_password = bcrypt.hash(password)
        user_doc = {"password": hashed_password}
        if email:
            user_doc["email"] = email
        if phone:
            user_doc["phone"] = phone

        users_collection.insert_one(user_doc)
        return jsonify({"success": True, "message": "Registration successful."}), 201

    except Exception as e:
        print("Error in registration:", e)
        return jsonify({"success": False, "message": "Internal server error."}), 500

###############################################################################
# OAuth Routes
###############################################################################
@app.route('/api/auth/google')
def google_login():
    """
    Initiates Google OAuth flow
    
    Redirects user to Google's authentication page
    """
    google = OAuth2Session(
        GOOGLE_CLIENT_ID,
        scope=["openid", "email", "profile"],
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    authorization_url, state = google.authorization_url(
        AUTHORIZATION_BASE_URL,
        access_type="offline",
        prompt="select_account"
    )

    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/api/auth/google/callback')
def google_callback():
    """
    Handles Google OAuth callback
    
    Receives authentication code from Google, exchanges for token,
    retrieves user info, and handles user creation/login
    """
    google = OAuth2Session(
        GOOGLE_CLIENT_ID,
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=session.get('oauth_state')
    )

    # Exchange authorization code for token
    token = google.fetch_token(
        TOKEN_URL,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorization_response=request.url
    )

    # Get user information using the token
    user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    email = user_info.get("email")
    google_id = user_info.get("sub")
    name = user_info.get("name", "")

    if not email:
        return jsonify({"success": False, "message": "Could not retrieve email from Google"}), 400

    # Create or update user in database
    existing_user = users_collection.find_one({"email": email})
    if not existing_user:
        users_collection.insert_one({
            "email": email,
            "google_id": google_id,
            "name": name,
            "password": None  # No password for OAuth users
        })
    else:
        users_collection.update_one(
            {"email": email},
            {"$set": {"google_id": google_id, "name": name}}
        )

    # Redirect to frontend with user info
    params = urlencode({"user": email})
    redirect_url = f"{FRONTEND_URL}/welcome?{params}"
    return redirect(redirect_url)

###############################################################################
# Testing and Utility Routes
###############################################################################
@app.route('/api/seed_user', methods=['POST'])
def seed_user():
    """
    Creates a test user for development/testing purposes
    """
    data = request.get_json()
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not (email and password):
        return jsonify({"success": False, "message": "Missing email or password."}), 400

    hashed_password = bcrypt.hash(password)
    users_collection.insert_one({
        "email": email,
        "phone": phone,
        "password": hashed_password
    })
    return jsonify({"success": True, "message": "Test user seeded."}), 201

@app.route('/api/reset_attempts', methods=['POST'])
def reset_attempts():
    """
    Resets all failed login attempts (for testing purposes)
    """
    global failed_login_attempts
    failed_login_attempts = {}
    return jsonify({"success": True, "message": "Attempts reset."}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)