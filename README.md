# Login Authentication System Setup Guide

This repository contains a full-stack authentication system with:
- React frontend with standard and OAuth login
- Flask backend API with MongoDB integration
- Selenium test suite for comprehensive testing

## Project Overview

**Authentication Features:**
- Email/phone & password login
- Google OAuth integration
- Brute force protection
- Form validation
- Error handling
- User registration

## Setup Instructions

### Prerequisites

- Node.js (v18+) and npm
- Python (v3.8+)
- MongoDB (v4+)
- Chrome browser (for Selenium tests)

### Backend Setup

1. **Create and activate Python virtual environment:**

```bash
cd backend
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

2. **Install backend dependencies:**
pip install -r requirements.txt

3. **Environment variables setup:**
FLASK_SECRET_KEY=your_secret_key_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MONGODB_URI=mongodb://localhost:27017/

### Frontend Setup
1.  **Install frontend dependencies:**
cd frontend
npm install
npm install bootstrap bootstrap-icons 


### Selenium Setup
2. **Create and activate Python virtual environment:**

```bash
cd selenium
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```
2.  **Install selenium dependencies:**
cd selenium
pip install -r requirements.txt


### MongoDB Setup
1. **Start MongoDB**
mongod --dbpath=/path/to/data/directory


## Running the Application

1.  **Start Backend Server**
cd backend
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

python app.py

 # The backend API will be available at http://localhost:5000.

2. **Start Frontend Development Server**
cd frontend
npm start

 # The React application will be available at http://localhost:3000.

3. **Running Tests**
cd selenium
python test_login.py
