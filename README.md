# Database-System

## Course Information  
This project is part of the **Database & Web Development** course taught by **Professor Yun-Cheng Tsai**.  
The course provides students with a comprehensive foundation in database implementation and full stack web development.  
It combines theoretical concepts with hands-on practice, enabling students to build dynamic, data-driven web applications.  

### Course Objectives  
1. **Database Implementation**: Gain practical experience with both **SQL** and **NoSQL** databases, understanding their use cases and best practices.  
2. **Web Development Skills**: Learn to build modern, interactive web applications with Python frameworks and React.  
3. **Integration of Frontend & Backend**: Apply full stack development principles to connect databases with web interfaces.  
4. **Practical Problem Solving**: Develop the ability to design, query, and manage databases to support real-world web applications.  

---

## Overview  
This repository contains assignments and projects completed throughout the course.  
Each homework (HW) emphasizes a core concept of database operations and web app development, progressing from SQL to NoSQL, and integrating frontend development with Python-based web frameworks.  

---

## Example Implementations  

### **HW1: Your First Full Stack Web App with SQL**  
**Folder:** [HW1](https://github.com/KyleHung7/Database-System/tree/main/HW1)
- **Focus**: Build a basic full stack web application connected to an SQL database.  
- **Key Concepts**:  
  - SQL schema creation  
  - Data insertion and retrieval  
  - Connecting SQL backend with frontend  

---

### **HW2: SQL CRUD Operations**  
**Folder:** `HW2`  
- **Focus**: Master **Create, Read, Update, Delete (CRUD)** operations with SQL.  
- **Key Concepts**:  
  - Writing SQL queries for each CRUD operation  
  - Implementing SQL operations in a web application  
  - Backend-frontend interaction for CRUD functionality  

---

### **HW3: Your First Full Stack Web App with NoSQL**  
**Folder:** `HW3`  
- **Focus**: Build a full stack web application using a **NoSQL** database.  
- **Key Concepts**:  
  - NoSQL database structure and document-based storage  
  - Performing queries in NoSQL  
  - Integrating NoSQL with a web frontend  

---

### **HW4: Query Data 3 (Delete with `deleteMany`)**  
**Folder:** `HW4`  
- **Focus**: Learn advanced NoSQL query operations with deletion.  
- **Key Concepts**:  
  - Using `db.collection.deleteMany()` to remove multiple documents  
  - Handling delete operations safely in a full stack environment  
  - Frontend-triggered delete operations with backend integration  

---

## Prerequisites  
- **Python** 3.10+  
- **SQL Database** (e.g., MySQL, PostgreSQL, SQLite)  
- **NoSQL Database** (e.g., MongoDB)  

---

## Installation Steps  
```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate    # Windows
source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Example: If using Flask + SQLAlchemy + PyMongo
pip install flask flask_sqlalchemy pymongo

