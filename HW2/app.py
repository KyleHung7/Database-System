from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import mysql.connector

# --- 1. 設定與初始化 ---

# 載入 .env 檔案中的環境變數
load_dotenv()

# 初始化 Flask 應用
app = Flask(__name__)

# 從環境變數讀取 SECRET_KEY，這對於 flash 訊息至關重要
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("錯誤：找不到 SECRET_KEY 環境變數。請在 .env 檔案中設定它。")

# --- 2. 資料庫連線函式 ---

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
        return None

# --- 3. 路由與視圖函式 (CRUD 邏輯) ---

# 主頁面：顯示所有病患 (READ with JOIN)
@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        flash('資料庫連線失敗，請檢查您的 .env 設定。', 'danger')
        return render_template('index.html', patients=[])
        
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT p.*, COUNT(c.condition_id) as condition_count
    FROM patients p
    LEFT JOIN conditions c ON p.patient_id = c.patient_id
    GROUP BY p.patient_id
    ORDER BY p.name;
    """
    cursor.execute(query)
    patients = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', patients=patients)

# 新增病患 (CREATE)
@app.route('/patient/new', methods=['GET', 'POST'])
def new_patient():
    if request.method == 'POST':
        name = request.form['name']
        birthdate = request.form['birthdate']
        gender = request.form['gender']
        contact_info = request.form['contact_info']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO patients (name, birthdate, gender, contact_info) VALUES (%s, %s, %s, %s)',
            (name, birthdate, gender, contact_info)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('病患資料已成功新增！', 'success')
        return redirect(url_for('index'))
    
    return render_template('patient_form.html', form_action='new_patient', patient=None)

# 編輯病患 (UPDATE)
@app.route('/patient/edit/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        birthdate = request.form['birthdate']
        gender = request.form['gender']
        contact_info = request.form['contact_info']
        
        cursor.execute(
            'UPDATE patients SET name=%s, birthdate=%s, gender=%s, contact_info=%s WHERE patient_id=%s',
            (name, birthdate, gender, contact_info, patient_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('病患資料已成功更新！', 'success')
        return redirect(url_for('index'))
        
    cursor.execute('SELECT * FROM patients WHERE patient_id = %s', (patient_id,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('patient_form.html', form_action='edit_patient', patient=patient)

# 刪除病患 (DELETE)
@app.route('/patient/delete/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM patients WHERE patient_id = %s', (patient_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('病患資料已成功刪除！', 'danger')
    return redirect(url_for('index'))

# 病患詳細頁面 (管理病情和治療的 CRUD)
@app.route('/patient/<int:patient_id>')
def patient_detail(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT * FROM patients WHERE patient_id = %s', (patient_id,))
    patient = cursor.fetchone()
    
    cursor.execute('SELECT * FROM conditions WHERE patient_id = %s ORDER BY diagnosis_date DESC', (patient_id,))
    conditions = cursor.fetchall()
    
    query_treatments = """
    SELECT t.*, c.condition_name 
    FROM treatments t
    JOIN conditions c ON t.condition_id = c.condition_id
    WHERE c.patient_id = %s
    ORDER BY t.start_date DESC
    """
    cursor.execute(query_treatments, (patient_id,))
    treatments = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template('patient_detail.html', patient=patient, conditions=conditions, treatments=treatments)

# 為病患新增病情 (CREATE)
@app.route('/patient/<int:patient_id>/condition/add', methods=['POST'])
def add_condition(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO conditions (patient_id, condition_name, diagnosis_date, severity) VALUES (%s, %s, %s, %s)',
        (patient_id, request.form['condition_name'], request.form['diagnosis_date'], request.form['severity'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash('病情已新增', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# 為病情新增治療 (CREATE)
@app.route('/patient/<int:patient_id>/treatment/add', methods=['POST'])
def add_treatment(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO treatments (condition_id, treatment_name, start_date, dosage) VALUES (%s, %s, %s, %s)',
        (request.form['condition_id'], request.form['treatment_name'], request.form['start_date'], request.form['dosage'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash('治療方案已新增', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))
    
# 刪除病情 (DELETE)
@app.route('/patient/<int:patient_id>/condition/delete/<int:condition_id>', methods=['POST'])
def delete_condition(patient_id, condition_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM conditions WHERE condition_id = %s', (condition_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('病情已刪除', 'danger')
    return redirect(url_for('patient_detail', patient_id=patient_id))
    
# 刪除治療 (DELETE)
@app.route('/patient/<int:patient_id>/treatment/delete/<int:treatment_id>', methods=['POST'])
def delete_treatment(patient_id, treatment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM treatments WHERE treatment_id = %s', (treatment_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('治療方案已刪除', 'danger')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# --- 4. 啟動應用程式 ---

if __name__ == '__main__':
    # debug=True 在開發時很有用，但在生產環境中應設為 False
    app.run(debug=True)