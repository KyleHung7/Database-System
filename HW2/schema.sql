-- schema.sql

DROP DATABASE IF EXISTS medical_db;
CREATE DATABASE medical_db;
USE medical_db;

-- Table for Patients
CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    birthdate DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    contact_info VARCHAR(100)
);

-- Table for Medical Conditions
CREATE TABLE conditions (
    condition_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    condition_name VARCHAR(100) NOT NULL,
    diagnosis_date DATE NOT NULL,
    severity VARCHAR(50),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- Table for Treatments
CREATE TABLE treatments (
    treatment_id INT AUTO_INCREMENT PRIMARY KEY,
    condition_id INT NOT NULL,
    treatment_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    dosage VARCHAR(100),
    FOREIGN KEY (condition_id) REFERENCES conditions(condition_id) ON DELETE CASCADE
);

-- Insert sample data
INSERT INTO patients (name, birthdate, gender, contact_info) VALUES
('John Doe', '1985-05-15', 'Male', '555-0101'),
('Jane Smith', '1992-08-22', 'Female', 'jane.smith@email.com'),
('Robert Brown', '1970-01-30', 'Male', '555-0102');

INSERT INTO conditions (patient_id, condition_name, diagnosis_date, severity) VALUES
(1, 'Hypertension', '2022-01-10', 'Moderate'),
(1, 'Type 2 Diabetes', '2023-03-15', 'Mild'),
(2, 'Allergic Rhinitis', '2021-09-01', 'Mild');

INSERT INTO treatments (condition_id, treatment_name, start_date, dosage) VALUES
(1, 'Lisinopril', '2022-01-11', '10mg daily'),
(2, 'Metformin', '2023-03-16', '500mg after meals'),
(3, 'Nasal Spray', '2021-09-01', 'Twice daily');