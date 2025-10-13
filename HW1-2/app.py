import os
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# Read database connection settings from environment variables
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

def get_db_connection():
    """Create and return a database connection"""
    conn = mysql.connector.connect(**db_config)
    return conn

# Home page (Read): display all patient records
@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patient_records ORDER BY created_at DESC")
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("index.html", records=records)

# Add new record page (shows the form)
@app.route("/add")
def add_form():
    return render_template("add_record.html")

# Handle the request to create a new record (Create)
@app.route("/create", methods=["POST"])
def create_record():
    name = request.form["patient_name"]
    dob = request.form["date_of_birth"]
    condition = request.form["condition_desc"]
    notes = request.form["notes"]

    conn = get_db_connection()
    cursor = conn.cursor()
    # Note: If date_of_birth is optional, handle empty string cases
    sql = """
        INSERT INTO patient_records (patient_name, date_of_birth, condition_desc, notes)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(sql, (name, dob if dob else None, condition, notes))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("index"))

# Edit record page (shows the form with existing data)
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

# Handle the request to update an existing record (Update)
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

# Handle the request to delete a record (Delete)
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
