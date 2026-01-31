"""
Seed Mock Data Script - Enhanced Version
Creates 100 users including 5 "Laundering Personas" with suspicious appeals
"""
import sys
from pathlib import Path
import random
from datetime import datetime, timedelta

server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

from src.database.sqlite_connector import SQLiteConnector

def seed_mock_data():
    """Generate 100 users with 5 laundering personas."""
    db = SQLiteConnector()
    
    # Use a single connection for the entire operation
    conn = db.get_connection()
    c = conn.cursor()
    
    # Enable WAL mode for better concurrency
    try:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA busy_timeout=30000")
    except:
        pass
    
    print("Clearing existing data...")
    try:
        c.execute("DELETE FROM transactions")
        c.execute("DELETE FROM users")
        c.execute("DELETE FROM auth_users WHERE email NOT LIKE '%@admin.com'")
        conn.commit()
        print("[OK] Cleared existing data\n")
    except Exception as e:
        print(f"[WARN] Error clearing data: {e}")
        conn.rollback()
    
    print("Creating 100 users...")
    
    # Regular users (95)
    first_names = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", 
                   "Ivy", "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Paul", 
                   "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier", "Yara", "Zoe"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", 
                  "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee"]
    
    users_created = []
    
    # Create 95 regular users
    print("Creating 95 regular users...")
    for i in range(1, 96):
        user_id = f"U{i:03d}"
        first = random.choice(first_names)
        last = random.choice(last_names)
        name = f"{first} {last}"
        
        risk_score = random.uniform(0.1, 0.6)
        balance = random.uniform(1000, 50000)
        account_age = random.randint(30, 2000)
        
        try:
            c.execute("""
                INSERT OR REPLACE INTO users (user_id, name, risk_score, account_age_days, balance, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, name, risk_score, account_age, balance, 'ACTIVE'))
        except Exception as e:
            print(f"[WARN] Error creating user {user_id}: {e}")
        
        users_created.append(user_id)
        
        if i % 20 == 0:
            conn.commit()
    
    conn.commit()
    print(f"[OK] Created 95 regular users")
    
    # Create 5 Laundering Personas with appeals
    print("\nCreating 5 Laundering Personas...")
    
    personas = [
        {
            "user_id": "U096",
            "name": "Carlos The Smurfer",
            "risk_score": 0.85,
            "balance": 150000,
            "account_age_days": 45,
            "typology": "Smurfing",
            "is_suspicious": 1,
            "status": "FROZEN",
            "appeal": "I run a small business and receive many small payments from customers. These are legitimate transactions."
        },
        {
            "user_id": "U097",
            "name": "Maria The Structurer",
            "risk_score": 0.88,
            "balance": 200000,
            "account_age_days": 30,
            "typology": "Structuring",
            "is_suspicious": 1,
            "status": "FROZEN",
            "appeal": "I was trying to avoid bank fees by keeping transactions under $10,000. I didn't know this was suspicious."
        },
        {
            "user_id": "U098",
            "name": "Viktor The Cycler",
            "risk_score": 0.92,
            "balance": 500000,
            "account_age_days": 60,
            "typology": "Circular Flow",
            "is_suspicious": 1,
            "status": "FROZEN",
            "appeal": "These are legitimate business transactions between my companies. I can provide documentation."
        },
        {
            "user_id": "U099",
            "name": "Layla The Launderer",
            "risk_score": 0.90,
            "balance": 300000,
            "account_age_days": 25,
            "typology": "Money Laundering",
            "is_suspicious": 1,
            "status": "FROZEN",
            "appeal": "I am an international trader. These are normal business operations for my industry."
        },
        {
            "user_id": "U100",
            "name": "Dmitri The Rapid-Exiter",
            "risk_score": 0.87,
            "balance": 250000,
            "account_age_days": 20,
            "typology": "High Velocity",
            "is_suspicious": 1,
            "status": "FROZEN",
            "appeal": "I am a day trader. High transaction volume is normal for my profession."
        }
    ]
    
    for persona in personas:
        try:
            c.execute("""
                INSERT OR REPLACE INTO users (user_id, name, risk_score, account_age_days, balance, status, typology, is_suspicious)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (persona["user_id"], persona["name"], persona["risk_score"], 
                  persona["account_age_days"], persona["balance"], persona["status"],
                  persona["typology"], persona["is_suspicious"]))
            
            # Create appeal record (stored in a simple appeals table or as metadata)
            # For now, we'll store it as a note that can be retrieved
            print(f"  {persona['user_id']} - {persona['name']} ({persona['typology']}) - Appeal: {persona['appeal'][:50]}...")
            
            users_created.append(persona["user_id"])
        except Exception as e:
            print(f"[WARN] Error creating persona {persona['user_id']}: {e}")
    
    conn.commit()
    print(f"[OK] Created 5 laundering personas with frozen accounts and appeals\n")
    
    # Create transactions
    print("Creating transactions...")
    transaction_count = 0
    
    # Regular transactions
    for i in range(200):
        source = random.choice(users_created)
        target = random.choice([u for u in users_created if u != source])
        amount = random.uniform(50, 5000)
        
        if random.random() < 0.1:
            amount = random.uniform(9000, 9999)
        
        tx_type = random.choice(["transfer", "payment", "wire"])
        tx_id = f"TX{i + 1:06d}"
        
        try:
            c.execute("""
                INSERT INTO transactions (transaction_id, source_user_id, target_user_id, 
                                      amount, currency, transaction_type, timestamp, status,
                                      is_suspicious, ai_risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, source, target, amount, "USD", tx_type, 
                  datetime.now(), "APPROVED", 0, 0.3))
            transaction_count += 1
        except Exception as e:
            print(f"[WARN] Error creating transaction: {e}")
        
        if (i + 1) % 50 == 0:
            conn.commit()
    
    conn.commit()
    
    # Smurfing pattern (U096) - many small transactions
    for i in range(15):
        target = random.choice([u for u in users_created if u != "U096"])
        amount = random.uniform(500, 2000)
        tx_id = f"TX{200 + i + 1:06d}"
        
        try:
            c.execute("""
                INSERT INTO transactions (transaction_id, source_user_id, target_user_id, 
                                      amount, currency, transaction_type, timestamp, status,
                                      is_suspicious, ai_risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, "U096", target, amount, "USD", "transfer", 
                  datetime.now() - timedelta(hours=random.randint(1, 48)), "FLAGGED", 1, 0.85))
            transaction_count += 1
        except Exception as e:
            print(f"[WARN] Error: {e}")
    
    # Structuring pattern (U097) - transactions near 10k
    for i in range(8):
        target = random.choice([u for u in users_created if u != "U097"])
        amount = random.uniform(9000, 9999)
        tx_id = f"TX{215 + i + 1:06d}"
        timestamp = datetime.now() - timedelta(hours=random.randint(1, 48))
        
        try:
            c.execute("""
                INSERT INTO transactions (transaction_id, source_user_id, target_user_id, 
                                      amount, currency, transaction_type, timestamp, status,
                                      is_suspicious, ai_risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, "U097", target, amount, "USD", "transfer", 
                  timestamp, "FLAGGED", 1, 0.88))
            transaction_count += 1
        except Exception as e:
            print(f"[WARN] Error: {e}")
    
    # Circular flow (U098, U099, U100)
    circular_users = ["U098", "U099", "U100"]
    for i in range(10):
        source = circular_users[i % 3]
        target = circular_users[(i + 1) % 3]
        amount = random.uniform(10000, 50000)
        tx_id = f"TX{223 + i + 1:06d}"
        
        try:
            c.execute("""
                INSERT INTO transactions (transaction_id, source_user_id, target_user_id, 
                                      amount, currency, transaction_type, timestamp, status,
                                      is_suspicious, ai_risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, source, target, amount, "USD", "wire", 
                  datetime.now() - timedelta(hours=random.randint(1, 72)), "FLAGGED", 1, 0.92))
            transaction_count += 1
        except Exception as e:
            print(f"[WARN] Error: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"[OK] Created {transaction_count} transactions")
    print("\n[SUCCESS] Mock data seeding completed!")
    print(f"  - Users: 100 (95 regular, 5 laundering personas)")
    print(f"  - Transactions: {transaction_count}")
    print(f"  - Frozen accounts with appeals: 5")
    print("\nLaundering Personas:")
    for persona in personas:
        print(f"  - {persona['user_id']}: {persona['name']} ({persona['typology']}) - Status: {persona['status']}")

if __name__ == "__main__":
    seed_mock_data()
