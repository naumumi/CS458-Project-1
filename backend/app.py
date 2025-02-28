import os
import pymongo
from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from passlib.hash import bcrypt
from requests_oauthlib import OAuth2Session
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = "YOUR_FLASK_SECRET_KEY"  # replace with a secure key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # allow http for local testing
CORS(app, supports_credentials=True)

# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["login_database"]
users_collection = db["users"]

###############################################################################
# In-Memory Failed Login Tracking for Brute Force
###############################################################################
failed_login_attempts = {}  # e.g. {"test@example.com": 3, "+1234567890": 2}
LOCKOUT_THRESHOLD = 5       # After 5 consecutive fails, lock out

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')

    # Check for existing user
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

    # Compare hashed password
    if user["password"] and bcrypt.verify(password, user["password"]):
        # Reset attempts on success
        failed_login_attempts[identifier] = 0

        # Mark session
        session['logged_in'] = True
        session['user'] = identifier
        return jsonify({"success": True, "message": "Login successful"}), 200
    else:
        # Wrong password, increment attempt count
        current_attempts = failed_login_attempts.get(identifier, 0) + 1
        failed_login_attempts[identifier] = current_attempts

        if current_attempts >= LOCKOUT_THRESHOLD:
            return jsonify({"success": False, "message": "Too many failed attempts"}), 200
        else:
            return jsonify({"success": False, "message": "Invalid password"}), 200

###############################################################################
# GOOGLE OAUTH
###############################################################################
GOOGLE_CLIENT_ID = "133456352418-o6fjcn4sjk06opgma3129ged0ajfvk27.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REDIRECT_URI = "http://localhost:5000/api/auth/google/callback"

AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

@app.route('/api/auth/google')
def google_login():
    """
    1) Redirect user to Google's OAuth 2.0 server for login
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
    Step 2: Google redirects back with a code. Exchange code for tokens,
            get user info, and log them in (create/update DB record).
    """
    google = OAuth2Session(
        GOOGLE_CLIENT_ID,
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=session.get('oauth_state')
    )

    # Exchange the authorization code for a token
    token = google.fetch_token(
        TOKEN_URL,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorization_response=request.url
    )

    # Use the token to get user info
    user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    email = user_info.get("email")
    google_id = user_info.get("sub")
    name = user_info.get("name", "")

    if not email:
        return jsonify({"success": False, "message": "Could not retrieve email from Google"}), 400

    # Upsert user into MongoDB
    existing_user = users_collection.find_one({"email": email})
    if not existing_user:
        users_collection.insert_one({
            "email": email,
            "google_id": google_id,
            "name": name,
            "password": None  # No password needed for Google-based login
        })
    else:
        users_collection.update_one(
            {"email": email},
            {"$set": {"google_id": google_id, "name": name}}
        )

    # Build the redirect URL with query parameters
    params = urlencode({"user": email})
    redirect_url = f"http://localhost:3000/welcome?{params}"
    return redirect(redirect_url)

###############################################################################
# Registration Endpoint
###############################################################################
@app.route('/api/register', methods=['POST'])
def register():
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

        # Hash the password and create the user document.
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
# SEED ENDPOINT (OPTIONAL) - For Creating a Test User
###############################################################################
@app.route('/api/seed_user', methods=['POST'])
def seed_user():
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
