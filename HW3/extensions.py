# extensions.py
from flask_login import LoginManager
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys

load_dotenv()

try:
    client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client.stock_portfolio_db
    print("Successfully connected to MongoDB.")
except Exception as e:
    print("FATAL: Could not connect to MongoDB. Please check your MONGO_URI and network access.", file=sys.stderr)
    print(f"Error details: {e}", file=sys.stderr)
    sys.exit(1)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"