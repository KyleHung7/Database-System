# db.py

import mysql.connector
import os

def get_db_connection():
    """建立並返回一個 MySQL 資料庫連線，設定從環境變數讀取"""
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME')
        )
        return connection
    except mysql.connector.Error as err:
        print(f"資料庫連線錯誤: {err}")
        # 在實際應用中，你可能希望更優雅地處理這個錯誤
        # 例如，返回一個錯誤頁面或日誌記錄
        return None