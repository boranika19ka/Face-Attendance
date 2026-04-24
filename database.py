import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_PATH = "data/attendance_system.db"

def init_db():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    # Default settings
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('start_time', '09:00')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'dark')")
    
    conn.commit()
    conn.close()

def add_student(student_id, name, department):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (student_id, name, department) VALUES (?, ?, ?)", 
                       (student_id, name, department))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def log_attendance(student_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # Log every scan (removed daily limit to show continuous history)
    cursor.execute("INSERT INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)", 
                   (student_id, date_str, time_str, status))
    conn.commit()
    conn.close()
    return True

def get_all_students():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    return df

def get_attendance_records():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT a.student_id, s.name, a.date, a.time, a.status 
    FROM attendance a 
    JOIN students s ON a.student_id = s.student_id
    ORDER BY a.date DESC, a.time DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_dashboard_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]
    
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date = ?", (today,))
    today_attendance = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date = ? AND status = 'Late'", (today,))
    late_today = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_students": total_students,
        "today_attendance": today_attendance,
        "late_today": late_today
    }

def update_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def delete_student(student_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Delete attendance first due to FK (though not strictly enforced in this schema)
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting student: {e}")
        return False
    finally:
        conn.close()

def update_student(student_id, name, department):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE students SET name = ?, department = ? WHERE student_id = ?", 
                       (name, department, student_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating student: {e}")
        return False
    finally:
        conn.close()

def delete_attendance_record(record_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def get_all_attendance_with_id():
    """Version of get_attendance_records that includes the internal ID for deletion"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT a.id, a.student_id, s.name, a.date, a.time, a.status 
    FROM attendance a 
    JOIN students s ON a.student_id = s.student_id
    ORDER BY a.date DESC, a.time DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

if __name__ == "__main__":
    init_db()
    print("Database initialized.")

def get_students_summary():
    """Returns students with their attendance statistics"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        s.student_id, 
        s.name, 
        s.department, 
        s.registration_date,
        COUNT(CASE WHEN a.status = 'On Time' THEN 1 END) as on_time_count,
        COUNT(CASE WHEN a.status = 'Late' THEN 1 END) as late_count
    FROM students s
    LEFT JOIN attendance a ON s.student_id = a.student_id
    GROUP BY s.student_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_attendance_trends():
    """Returns attendance counts grouped by date and status"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date, status, COUNT(*) as count
    FROM attendance
    GROUP BY date, status
    ORDER BY date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_warning_list(threshold=3):
    """Returns students who have been late more than the threshold"""
    conn = sqlite3.connect(DB_PATH)
    query = f"""
    SELECT s.student_id, s.name, s.department, COUNT(a.id) as late_count
    FROM students s
    JOIN attendance a ON s.student_id = a.student_id
    WHERE a.status = 'Late'
    GROUP BY s.student_id
    HAVING late_count >= {threshold}
    ORDER BY late_count DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
