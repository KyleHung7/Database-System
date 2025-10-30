# extensions.py
from flask_login import LoginManager
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
import certifi # <-- 引入 certifi

load_dotenv()

try:
    # 取得 certifi 提供的最新 CA 憑證檔案的路徑
    ca = certifi.where()
    
    # 在 MongoClient 中，使用 tlsCAFile 參數來強制使用這個憑證檔案
    client = MongoClient(
        os.getenv("MONGO_URI"),
        tlsCAFile=ca, # <-- 這是解決 SSL 問題的關鍵
        serverSelectionTimeoutMS=5000
    )
    
    client.server_info()
    db = client.stock_portfolio_db
    print("Successfully connected to MongoDB using certifi.")
except Exception as e:
    print("FATAL: Could not connect to MongoDB. Please check your MONGO_URI and network access.", file=sys.stderr)
    print(f"Error details: {e}", file=sys.stderr)
    sys.exit(1)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'