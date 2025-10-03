import os
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

app = Flask(__name__)

# 從環境變數讀取資料庫連線設定
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

def get_db_connection():
    """建立並返回資料庫連線"""
    conn = mysql.connector.connect(**db_config)
    return conn

# 首頁 (Read)：顯示所有病患紀錄
@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patient_records ORDER BY created_at DESC")
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("index.html", records=records)

# 新增紀錄的頁面 (顯示表單)
@app.route("/add")
def add_form():
    return render_template("add_record.html")

# 處理新增紀錄的請求 (Create)
@app.route("/create", methods=["POST"])
def create_record():
    name = request.form["patient_name"]
    dob = request.form["date_of_birth"]
    condition = request.form["condition_desc"]
    notes = request.form["notes"]

    conn = get_db_connection()
    cursor = conn.cursor()
    # 注意：如果 date_of_birth 是可選的，你可能需要處理空字串的情況
    sql = "INSERT INTO patient_records (patient_name, date_of_birth, condition_desc, notes) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (name, dob if dob else None, condition, notes))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("index"))

# 編輯紀錄的頁面 (顯示已有資料的表單)
@app.route("/edit/<int:record_id>")
def edit_form(record_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patient_records WHERE id = %s", (record_id,))
    record = cursor.fetchone()
    cursor.close()
    conn.close()
    if record:
        return render_template("edit_record.html", record=record)
    return "Record not found", 404

# 處理更新紀錄的請求 (Update)
@app.route("/update/<int:record_id>", methods=["POST"])
def update_record(record_id):
    name = request.form["patient_name"]
    dob = request.form["date_of_birth"]
    condition = request.form["condition_desc"]
    notes = request.form["notes"]

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        UPDATE patient_records 
        SET patient_name = %s, date_of_birth = %s, condition_desc = %s, notes = %s 
        WHERE id = %s
    """
    cursor.execute(sql, (name, dob if dob else None, condition, notes, record_id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("index"))

# 處理刪除紀錄的請求 (Delete)
@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patient_records WHERE id = %s", (record_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)