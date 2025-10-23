# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import mysql.connector

# --- 1. Setup and Initialization ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("ERROR: SECRET_KEY not found in environment variables. Please set it in your .env file.")

# --- 2. Database Connection Function ---
def get_db_connection():
    """Establishes and returns a MySQL database connection using credentials from environment variables."""
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME')
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# --- 3. Routes and View Functions (CRUD Logic) ---

# Main Page: Display all patients (READ with JOIN)
@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed. Please check your .env configuration.', 'danger')
        return render_template('index.html', patients=[])
    
    cursor = conn.cursor(dictionary=True)
    # SQL JOIN Query: Select all patients and count their number of conditions
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

# Add a new patient (CREATE)
@app.route('/patient/new', methods=['GET', 'POST'])
def new_patient():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO patients (name, birthdate, gender, contact_info) VALUES (%s, %s, %s, %s)',
            (request.form['name'], request.form['birthdate'], request.form['gender'], request.form['contact_info'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Patient created successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('patient_form.html', form_action='new_patient', patient=None)

# Edit an existing patient (UPDATE)
@app.route('/patient/edit/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        cursor.execute(
            'UPDATE patients SET name=%s, birthdate=%s, gender=%s, contact_info=%s WHERE patient_id=%s',
            (request.form['name'], request.form['birthdate'], request.form['gender'], request.form['contact_info'], patient_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Patient details updated successfully!', 'success')
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM patients WHERE patient_id = %s', (patient_id,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('patient_form.html', form_action='edit_patient', patient=patient)

# Delete a patient (DELETE)
@app.route('/patient/delete/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # ON DELETE CASCADE will handle associated conditions and treatments
    cursor.execute('DELETE FROM patients WHERE patient_id = %s', (patient_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Patient and all associated records deleted successfully.', 'danger')
    return redirect(url_for('index'))

# Patient detail page (managing conditions and treatments)
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

# Add a condition for a patient (CREATE)
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
    flash('Condition added successfully.', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Add a treatment for a condition (CREATE)
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
    flash('Treatment plan added successfully.', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))
    
# Delete a condition (DELETE)
@app.route('/patient/<int:patient_id>/condition/delete/<int:condition_id>', methods=['POST'])
def delete_condition(patient_id, condition_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM conditions WHERE condition_id = %s', (condition_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Condition deleted successfully.', 'danger')
    return redirect(url_for('patient_detail', patient_id=patient_id))
    
# Delete a treatment (DELETE)
@app.route('/patient/<int:patient_id>/treatment/delete/<int:treatment_id>', methods=['POST'])
def delete_treatment(patient_id, treatment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM treatments WHERE treatment_id = %s', (treatment_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Treatment plan deleted successfully.', 'danger')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# --- 4. Run the Application ---
if __name__ == '__main__':
    # debug=True is useful for development. It should be set to False in production.
    app.run(debug=True)