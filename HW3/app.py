import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

app = Flask(__name__)
# Flash 訊息需要設定一個 secret key
app.secret_key = os.getenv("SECRET_KEY", "default-secret-key")

# --- 從環境變數讀取設定 ---
MONGO_URI = os.getenv("MONGO_URI")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# --- MongoDB 連線設定 ---
try:
    client = MongoClient(MONGO_URI)
    db = client.stock_db
    stocks_collection = db.stocks
    # 測試連線
    client.server_info() 
except Exception as e:
    print(f"無法連接到 MongoDB: {e}")
    # 在實際應用中，你可能希望在這裡處理錯誤，而不是讓應用崩潰
    
# --- 路由 (Routes) ---

@app.route('/')
def index():
    """首頁：顯示已儲存的投資組合，並可搜尋已儲存的股票"""
    query = request.args.get('query', '')
    try:
        if query:
            search_filter = {
                "$or": [
                    {"symbol": {"$regex": query, "$options": "i"}},
                    {"name": {"$regex": query, "$options": "i"}}
                ]
            }
            stocks = list(stocks_collection.find(search_filter))
        else:
            stocks = list(stocks_collection.find({}))
    except Exception as e:
        flash(f"讀取資料庫時發生錯誤: {e}", "danger")
        stocks = []
    return render_template('index.html', stocks=stocks, search_query=query)

@app.route('/search', methods=['GET', 'POST'])
def search_stock():
    """查詢即時股價的頁面"""
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').strip().upper()
        if not symbol:
            flash("請輸入股票代號。", "warning")
            return redirect(url_for('search_stock'))

        if not FINNHUB_API_KEY:
            flash("Finnhub API 金鑰未設定，請檢查您的 .env 檔案。", "danger")
            return redirect(url_for('search_stock'))

        try:
            # 查詢報價 (Quote)
            quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
            quote_res = requests.get(quote_url, timeout=10)
            quote_res.raise_for_status()
            quote_data = quote_res.json()

            # 查詢公司資訊 (Profile)
            profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API_KEY}"
            profile_res = requests.get(profile_url, timeout=10)
            profile_res.raise_for_status()
            profile_data = profile_res.json()

            if not profile_data or quote_data.get('c') == 0:
                flash(f"找不到股票代號 '{symbol}' 的資料，請確認代號是否正確 (例如: AAPL, 2330.TW)。", "danger")
                return redirect(url_for('search_stock'))

            stock_info = {
                "symbol": symbol,
                "name": profile_data.get('name', 'N/A'),
                "price": quote_data.get('c', 0.0),
                "logo": profile_data.get('logo', '')
            }
            return render_template('search_result.html', stock=stock_info)

        except requests.exceptions.RequestException as e:
            flash(f"API 請求失敗，請稍後再試。錯誤: {e}", "danger")
            return redirect(url_for('search_stock'))
        
    return render_template('search.html')

@app.route('/add', methods=['POST'])
def add_stock():
    """從查詢結果頁面，將決策後的股票資訊新增到投資組合"""
    try:
        stock_data = {
            "symbol": request.form.get('symbol').upper(),
            "name": request.form.get('name'),
            "price": float(request.form.get('price')),
            "notes": request.form.get('notes')
        }
        stocks_collection.insert_one(stock_data)
        flash(f"已成功將 {stock_data['symbol']} 加入您的投資組合！", "success")
    except Exception as e:
        flash(f"新增失敗: {e}", "danger")
        
    return redirect(url_for('index'))

@app.route('/edit/<stock_id>', methods=['GET', 'POST'])
def edit_stock(stock_id):
    """編輯已儲存的股票紀錄"""
    try:
        stock = stocks_collection.find_one({"_id": ObjectId(stock_id)})
        if not stock:
            flash("找不到該筆紀錄。", "warning")
            return redirect(url_for('index'))

        if request.method == 'POST':
            updated_data = {
                "$set": {
                    "symbol": request.form.get('symbol').upper(),
                    "name": request.form.get('name'),
                    "price": float(request.form.get('price')),
                    "notes": request.form.get('notes')
                }
            }
            stocks_collection.update_one({"_id": ObjectId(stock_id)}, updated_data)
            flash("紀錄已更新", "success")
            return redirect(url_for('index'))
        
        return render_template('edit_stock.html', stock=stock)
    except Exception as e:
        flash(f"操作失敗: {e}", "danger")
        return redirect(url_for('index'))

@app.route('/delete/<stock_id>', methods=['POST'])
def delete_stock(stock_id):
    """刪除已儲存的股票紀錄"""
    try:
        result = stocks_collection.delete_one({"_id": ObjectId(stock_id)})
        if result.deleted_count > 0:
            flash("紀錄已刪除", "info")
        else:
            flash("找不到要刪除的紀錄", "warning")
    except Exception as e:
        flash(f"刪除失敗: {e}", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)