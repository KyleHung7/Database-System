from flask import Flask, render_template, request
import mysql.connector
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()  # Load .env file

# MySQL connection config from environment variables
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}

@app.route('/', methods=['GET', 'POST'])
def index():
    filter_date = request.form.get('filter_date')
    sort_order = request.form.get('sort_order', 'ASC')
    keyword = request.form.get('keyword')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT v.visit_id, p.first_name, p.last_name, d.doctor_name, v.visit_date, v.diagnosis, v.notes
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        JOIN doctors d ON v.doctor_id = d.doctor_id
        WHERE 1=1
    """
    params = []

    if filter_date:
        query += " AND DATE(v.visit_date) = %s"
        params.append(filter_date)

    if keyword:
        query += " AND v.diagnosis LIKE %s"
        params.append(f"%{keyword}%")

    query += f" ORDER BY v.visit_date {sort_order}"

    cursor.execute(query, params)
    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('index.html', records=records,
                           filter_date=filter_date, sort_order=sort_order, keyword=keyword)

if __name__ == '__main__':
    app.run(debug=True)
