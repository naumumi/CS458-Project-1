import os
import pymongo
from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from passlib.hash import bcrypt
from requests_oauthlib import OAuth2Session

app = Flask(__name__)
app.secret_key = "YOUR_FLASK_SECRET_KEY"  # replace with a secure key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # allow http for local testing
CORS(app, supports_credentials=True)

# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["login_database"]
users_collection = db["users"]

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')

    # Find user by email or phone
    user = users_collection.find_one({
        "$or": [
            {"email": identifier},
            {"phone": identifier}
        ]
    })

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 200

    # Compare hashed password
    if bcrypt.verify(password, user["password"]):
        return jsonify({"success": True, "message": "Login successful"}), 200
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
    2) User returns from Google with a code. Exchange for an access token,
       retrieve user info, store in DB, and redirect to React with a success message.
    """
    google = OAuth2Session(
        GOOGLE_CLIENT_ID,
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=session.get('oauth_state')
    )

    # Exchange the auth code for a token
    token = google.fetch_token(
        TOKEN_URL,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorization_response=request.url
    )

    # Get user info
    user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    email = user_info.get("email")
    google_id = user_info.get("sub")
    name = user_info.get("name", "")

    if not email:
        return jsonify({"success": False, "message": "Could not retrieve email"}), 400

    # Upsert user in Mongo
    existing_user = users_collection.find_one({"email": email})
    if not existing_user:
        users_collection.insert_one({
            "email": email,
            "google_id": google_id,
            "name": name,
            "password": None  # no password for Google-based user
        })
    else:
        users_collection.update_one(
            {"email": email},
            {"$set": {"google_id": google_id, "name": name}}
        )

    # For demonstration: show an alert and redirect to the React app
    return f"""
    <script>
        alert("Google Login successful!\\nUser: {email}");
        window.location.href = "http://localhost:3000";
    </script>
    """

if __name__ == '__main__':
    app.run(debug=True, port=5000)
