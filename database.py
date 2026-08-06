"""
database.py
Handles all SQLite database setup and connection for the
School / College Management System.
"""

import sqlite3
import os

DB_NAME = "school.db"


def get_db_path():
    """Store the DB next to the executable/script."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_NAME)


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they do not already exist."""
    conn = get_connection()
    cur = conn.cursor()

    # ---------------- Classes ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session TEXT,
            class_name TEXT NOT NULL,
            section TEXT,
            class_teacher_id INTEGER,
            FOREIGN KEY (class_teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        )
    """)

    # ---------------- Teachers ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_code TEXT UNIQUE,
            name TEXT NOT NULL,
            cnic TEXT,
            qualification TEXT,
            subject TEXT,
            mobile TEXT,
            address TEXT,
            joining_date TEXT,
            salary REAL DEFAULT 0,
            status TEXT DEFAULT 'Active'
        )
    """)

    # ---------------- Students ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE,
            roll_no TEXT,
            reg_no TEXT,
            name TEXT NOT NULL,
            father_name TEXT,
            cnic_bform TEXT,
            gender TEXT,
            dob TEXT,
            mobile TEXT,
            address TEXT,
            admission_date TEXT,
            class_id INTEGER,
            section TEXT,
            session TEXT,
            photo_path TEXT,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
        )
    """)

    # ---------------- Subjects ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            subject_code TEXT,
            class_id INTEGER,
            teacher_id INTEGER,
            FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        )
    """)

    # ---------------- Attendance ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,  -- Present / Absent / Leave
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, date)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS teacher_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
            UNIQUE(teacher_id, date)
        )
    """)

    # ---------------- Fee Structure ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fee_structure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            admission_fee REAL DEFAULT 0,
            monthly_fee REAL DEFAULT 0,
            exam_fee REAL DEFAULT 0,
            annual_charges REAL DEFAULT 0,
            misc_fee REAL DEFAULT 0,
            FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
        )
    """)

    # ---------------- Fee Collection ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fee_collection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_no TEXT UNIQUE,
            student_id INTEGER NOT NULL,
            month TEXT,
            year TEXT,
            amount REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            fine REAL DEFAULT 0,
            total_paid REAL DEFAULT 0,
            date TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    # ---------------- Challans ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS challans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challan_no TEXT UNIQUE,
            student_id INTEGER NOT NULL,
            month TEXT,
            year TEXT,
            amount REAL DEFAULT 0,
            due_date TEXT,
            status TEXT DEFAULT 'Unpaid',
            generated_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    # ---------------- Exams ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_name TEXT NOT NULL,
            exam_type TEXT,   -- Monthly Test / Mid-Term / Final-Term
            class_id INTEGER,
            exam_date TEXT,
            FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
        )
    """)

    # ---------------- Marks ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            marks_obtained REAL DEFAULT 0,
            total_marks REAL DEFAULT 100,
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            UNIQUE(exam_id, student_id, subject_id)
        )
    """)

    # ---------------- Users (login / roles) ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'Admin'   -- Admin / Teacher / Accountant / Viewer
        )
    """)

    # ---------------- Settings (key/value) ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()

    # Seed a default admin user if none exists
    cur.execute("SELECT COUNT(*) as c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "Admin"),
        )

    # Seed default settings
    default_settings = {
        "school_name": "My School / College",
        "school_address": "",
        "school_phone": "",
        "current_session": "2025-2026",
    }
    for k, v in default_settings.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()


def get_setting(key, default=""):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()
