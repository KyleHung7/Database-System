-- schema.sql

CREATE DATABASE medical_db;

USE medical_db;

CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    birthdate DATE NOT NULL,
    gender ENUM('男', '女', '其他') NOT NULL,
    contact_info VARCHAR(100)
);

CREATE TABLE conditions (
    condition_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    condition_name VARCHAR(100) NOT NULL,
    diagnosis_date DATE NOT NULL,
    severity VARCHAR(50),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

CREATE TABLE treatments (
    treatment_id INT AUTO_INCREMENT PRIMARY KEY,
    condition_id INT NOT NULL,
    treatment_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    dosage VARCHAR(100),
    FOREIGN KEY (condition_id) REFERENCES conditions(condition_id) ON DELETE CASCADE
);

INSERT INTO patients (name, birthdate, gender, contact_info) VALUES
('王大明', '1985-05-15', '男', '0912-345678'),
('陳小美', '1992-08-22', '女', '0987-654321'),
('林志強', '1970-01-30', '男', '0933-111222');

INSERT INTO conditions (patient_id, condition_name, diagnosis_date, severity) VALUES
(1, '高血壓', '2022-01-10', '中度'),
(1, '糖尿病', '2023-03-15', '輕度'),
(2, '過敏性鼻炎', '2021-09-01', '輕度');

INSERT INTO treatments (condition_id, treatment_name, start_date, dosage) VALUES
(1, '降血壓藥 A', '2022-01-11', '每日 5mg'),
(2, '血糖控制藥物 B', '2023-03-16', '每日飯後 500mg'),
(3, '抗組織胺噴劑', '2021-09-01', '每日兩次');