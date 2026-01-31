"""Seed script for SQLite database."""
import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
server_dir = script_dir.parent / "server"
sys.path.insert(0, str(server_dir))

def main():
    from src.database.sqlite_connector import SQLiteConnector
    
    db_path = str(script_dir / "fraud_detection.db")
    
    if "--clear" in sys.argv and os.path.exists(db_path):
        os.remove(db_path)
        print(f"Cleared: {db_path}")
    
    db = SQLiteConnector(db_path=db_path)
    
    users = [
        ("U001", "Alice Johnson", 0.1, 1200),
        ("U002", "Bob Smith", 0.15, 890),
        ("U003", "Carol Williams", 0.2, 650),
        ("U004", "David Brown", 0.12, 1450),
        ("U005", "Eve Davis", 0.18, 320),
        ("U006", "Frank Miller", 0.45, 180),
        ("U007", "Grace Wilson", 0.5, 90),
        ("U008", "Henry Moore", 0.55, 120),
        ("U009", "Ivan Taylor", 0.85, 45),
        ("U010", "Julia Anderson", 0.78, 60),
        ("U011", "Kevin Thomas", 0.82, 30),
        ("U012", "Laura Jackson", 0.9, 15),
        ("U013", "Mike White", 0.65, 200),
        ("U014", "Nancy Harris", 0.7, 75),
        ("U015", "Oscar Martin", 0.88, 20),
    ]
    
    print("Creating users...")
    for uid, name, risk, age in users:
        db.create_user(uid, name, risk, age)
        print(f"  {uid} - {name}")
    
    transactions = [
        ("U001", "U002", 500.0, "payment"),
        ("U002", "U003", 250.0, "transfer"),
        ("U003", "U004", 1000.0, "payment"),
        ("U004", "U005", 750.0, "transfer"),
        ("U001", "U005", 300.0, "payment"),
        ("U009", "U010", 9500.0, "transfer"),
        ("U010", "U011", 9200.0, "transfer"),
        ("U011", "U009", 8900.0, "transfer"),
        ("U012", "U014", 15000.0, "wire"),
        ("U014", "U015", 14500.0, "wire"),
        ("U015", "U012", 14000.0, "wire"),
        ("U006", "U007", 5000.0, "transfer"),
        ("U007", "U008", 4800.0, "transfer"),
        ("U008", "U013", 4600.0, "transfer"),
        ("U013", "U006", 4400.0, "transfer"),
        ("U001", "U006", 200.0, "payment"),
        ("U002", "U009", 150.0, "payment"),
        ("U003", "U007", 350.0, "transfer"),
        ("U005", "U010", 100.0, "payment"),
        ("U004", "U001", 600.0, "refund"),
        ("U007", "U002", 180.0, "payment"),
        ("U013", "U003", 420.0, "transfer"),
        ("U008", "U005", 280.0, "payment"),
        ("U009", "U012", 25000.0, "wire"),
        ("U012", "U015", 24000.0, "wire"),
        ("U015", "U009", 23000.0, "wire"),
        ("U010", "U001", 50.0, "payment"),
        ("U011", "U002", 75.0, "payment"),
        ("U014", "U004", 90.0, "payment"),
    ]
    
    print("\nCreating transactions...")
    for src, tgt, amt, ttype in transactions:
        db.create_transaction(src, tgt, amt, "USD", ttype)
        print(f"  {src} -> {tgt}: ${amt}")
    
    print(f"\n✅ Done!")
    print(f"   Database: {db_path}")
    print(f"   Users: {len(users)}")
    print(f"   Transactions: {len(transactions)}")
    
    high_risk = db.get_high_risk_users(0.7)
    print(f"   High-risk users: {len(high_risk)}")
    
    db.close()

if __name__ == "__main__":
    main()