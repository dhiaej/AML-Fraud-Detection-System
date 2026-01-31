"""
Database Migration Script
Adds missing columns to transactions and users tables
"""
import sys
from pathlib import Path
import sqlite3

server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

from src.database.sqlite_connector import SQLiteConnector

def migrate_database():
    """Migrate database to add new columns."""
    db = SQLiteConnector()
    conn = db.get_connection()
    c = conn.cursor()
    
    print("Starting database migration...")
    
    # Migrate transactions table
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT 'PENDING'")
        print("[OK] Added 'status' column to transactions")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[OK] 'status' column already exists in transactions")
        else:
            print(f"[WARN] Error adding status: {e}")
    
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN is_suspicious INTEGER DEFAULT 0")
        print("[OK] Added 'is_suspicious' column to transactions")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[OK] 'is_suspicious' column already exists in transactions")
        else:
            print(f"[WARN] Error adding is_suspicious: {e}")
    
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN ai_risk_score REAL DEFAULT 0.0")
        print("[OK] Added 'ai_risk_score' column to transactions")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[OK] 'ai_risk_score' column already exists in transactions")
        else:
            print(f"[WARN] Error adding ai_risk_score: {e}")
    
    # Update existing transactions status
    try:
        c.execute("UPDATE transactions SET status = 'APPROVED' WHERE status = 'SUCCESS'")
        c.execute("UPDATE transactions SET status = 'PENDING' WHERE status IS NULL OR status = ''")
        print("[OK] Updated existing transaction statuses")
    except Exception as e:
        print(f"[WARN] Error updating transaction statuses: {e}")
    
    # Migrate users table
    try:
        c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'ACTIVE'")
        print("[OK] Added 'status' column to users")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[OK] 'status' column already exists in users")
        else:
            print(f"[WARN] Error adding status: {e}")
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
        print("[OK] Added 'balance' column to users")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[OK] 'balance' column already exists in users")
        else:
            print(f"[WARN] Error adding balance: {e}")
    
    # Update existing users status
    try:
        c.execute("UPDATE users SET status = 'ACTIVE' WHERE status IS NULL OR status = ''")
        print("[OK] Updated existing user statuses")
    except Exception as e:
        print(f"[WARN] Error updating user statuses: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n[SUCCESS] Database migration completed!")

if __name__ == "__main__":
    migrate_database()
