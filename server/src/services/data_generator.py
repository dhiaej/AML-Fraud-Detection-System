"""
Advanced Data Generator for Money Laundering Detection
Generates realistic financial crime typologies for testing and training.
"""

import sqlite3
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import math


class FinancialCrimeDataGenerator:
    """
    Generates synthetic financial data with injected money laundering patterns.
    
    Typologies implemented:
    - Smurfing (structuring deposits)
    - Rapid Movement (quick in/out)
    - Circular Flows (layering)
    - Structuring (threshold avoidance)
    """
    
    REPORTING_THRESHOLD = 10000  # CTR threshold
    STRUCTURING_AMOUNTS = [9900, 9800, 9700, 9500, 9200, 8900, 8500]
    
    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
        "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
        "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
        "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
    ]
    
    TRANSACTION_TYPES = [
        "wire_transfer", "ach_transfer", "cash_deposit", "cash_withdrawal",
        "crypto_buy", "crypto_sell", "check_deposit", "internal_transfer",
        "international_wire", "peer_to_peer"
    ]
    
    CURRENCIES = ["USD", "EUR", "GBP", "CAD", "MXN", "BTC", "ETH"]
    
    def __init__(self, db_path: str = "data/fraud_detection.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # Track generated entities for pattern injection
        self.users: List[Dict] = []
        self.transactions: List[Dict] = []
        self.kingpins: List[str] = []
        self.mules: List[str] = []
        self.smurfs: List[str] = []
        self.structurers: List[str] = []
        self.ring_members: List[str] = []
        
    def _init_database(self):
        """Initialize database with enhanced schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Drop existing tables for fresh generation
        c.execute("DROP TABLE IF EXISTS transactions")
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS alerts")
        c.execute("DROP TABLE IF EXISTS typology_labels")
        
        # Enhanced users table
        c.execute("""
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                risk_score REAL DEFAULT 0.1,
                account_age_days INTEGER DEFAULT 0,
                account_type TEXT DEFAULT 'personal',
                country TEXT DEFAULT 'US',
                is_pep INTEGER DEFAULT 0,
                kyc_verified INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                -- Labels for supervised learning
                is_suspicious INTEGER DEFAULT 0,
                typology TEXT DEFAULT NULL
            )
        """)
        
        # Enhanced transactions table
        c.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE,
                source_user_id TEXT NOT NULL,
                target_user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                transaction_type TEXT DEFAULT 'wire_transfer',
                timestamp TIMESTAMP NOT NULL,
                -- Additional features for ML
                is_international INTEGER DEFAULT 0,
                source_country TEXT DEFAULT 'US',
                target_country TEXT DEFAULT 'US',
                description TEXT,
                -- Labels for supervised learning
                is_suspicious INTEGER DEFAULT 0,
                typology TEXT DEFAULT NULL,
                FOREIGN KEY (source_user_id) REFERENCES users(user_id),
                FOREIGN KEY (target_user_id) REFERENCES users(user_id)
            )
        """)
        
        # Alerts table for detected patterns
        c.execute("""
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                user_id TEXT,
                transaction_ids TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'open'
            )
        """)
        
        # Typology labels for training
        c.execute("""
            CREATE TABLE typology_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                typology TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                description TEXT
            )
        """)
        
        # Create indexes
        c.execute("CREATE INDEX idx_tx_source ON transactions(source_user_id)")
        c.execute("CREATE INDEX idx_tx_target ON transactions(target_user_id)")
        c.execute("CREATE INDEX idx_tx_timestamp ON transactions(timestamp)")
        c.execute("CREATE INDEX idx_tx_amount ON transactions(amount)")
        c.execute("CREATE INDEX idx_users_risk ON users(risk_score)")
        
        conn.commit()
        conn.close()
        
    def _generate_user_id(self) -> str:
        """Generate unique user ID."""
        return f"U{len(self.users) + 1:04d}"
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        return f"TX{len(self.transactions) + 1:06d}"
    
    def _random_name(self) -> str:
        """Generate random full name."""
        return f"{random.choice(self.FIRST_NAMES)} {random.choice(self.LAST_NAMES)}"
    
    def _random_timestamp(self, start: datetime, end: datetime) -> datetime:
        """Generate random timestamp between start and end."""
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)
    
    def generate_legitimate_users(self, count: int = 400) -> List[Dict]:
        """Generate normal, legitimate users."""
        print(f"Generating {count} legitimate users...")
        
        for _ in range(count):
            user = {
                "user_id": self._generate_user_id(),
                "name": self._random_name(),
                "risk_score": random.uniform(0.05, 0.3),  # Low risk
                "account_age_days": random.randint(180, 3650),  # 6 months to 10 years
                "account_type": random.choice(["personal", "business", "personal", "personal"]),
                "country": random.choice(["US", "US", "US", "CA", "GB", "DE"]),
                "is_pep": 0,
                "kyc_verified": 1,
                "is_suspicious": 0,
                "typology": None
            }
            self.users.append(user)
            
        return self.users[-count:]
    
    def generate_suspicious_users(self) -> List[Dict]:
        """Generate users involved in money laundering."""
        print("Generating suspicious user network...")
        
        # Generate Kingpins (money laundering bosses)
        for i in range(3):
            user = {
                "user_id": self._generate_user_id(),
                "name": self._random_name(),
                "risk_score": random.uniform(0.7, 0.95),
                "account_age_days": random.randint(30, 365),
                "account_type": "business",
                "country": random.choice(["US", "MX", "PA"]),
                "is_pep": random.choice([0, 1]),
                "kyc_verified": 1,
                "is_suspicious": 1,
                "typology": "kingpin"
            }
            self.users.append(user)
            self.kingpins.append(user["user_id"])
        
        # Generate Mules (money collectors)
        for i in range(10):
            user = {
                "user_id": self._generate_user_id(),
                "name": self._random_name(),
                "risk_score": random.uniform(0.5, 0.8),
                "account_age_days": random.randint(30, 180),
                "account_type": "personal",
                "country": "US",
                "is_pep": 0,
                "kyc_verified": 1,
                "is_suspicious": 1,
                "typology": "mule"
            }
            self.users.append(user)
            self.mules.append(user["user_id"])
        
        # Generate Smurfs (small deposit makers)
        for i in range(30):
            user = {
                "user_id": self._generate_user_id(),
                "name": self._random_name(),
                "risk_score": random.uniform(0.3, 0.6),
                "account_age_days": random.randint(60, 365),
                "account_type": "personal",
                "country": "US",
                "is_pep": 0,
                "kyc_verified": random.choice([0, 1]),
                "is_suspicious": 1,
                "typology": "smurf"
            }
            self.users.append(user)
            self.smurfs.append(user["user_id"])
        
        # Generate Structurers (threshold avoiders)
        for i in range(15):
            user = {
                "user_id": self._generate_user_id(),
                "name": self._random_name(),
                "risk_score": random.uniform(0.4, 0.7),
                "account_age_days": random.randint(90, 730),
                "account_type": random.choice(["personal", "business"]),
                "country": "US",
                "is_pep": 0,
                "kyc_verified": 1,
                "is_suspicious": 1,
                "typology": "structurer"
            }
            self.users.append(user)
            self.structurers.append(user["user_id"])
        
        # Generate Ring Members (circular flow participants)
        for i in range(20):
            user = {
                "user_id": self._generate_user_id(),
                "name": self._random_name(),
                "risk_score": random.uniform(0.5, 0.85),
                "account_age_days": random.randint(30, 365),
                "account_type": random.choice(["personal", "business"]),
                "country": random.choice(["US", "MX", "CA", "PA"]),
                "is_pep": 0,
                "kyc_verified": 1,
                "is_suspicious": 1,
                "typology": "ring_member"
            }
            self.users.append(user)
            self.ring_members.append(user["user_id"])
        
        # Fill remaining to reach target
        remaining = 500 - len(self.users)
        if remaining > 0:
            self.generate_legitimate_users(remaining)
            
        return [u for u in self.users if u["is_suspicious"] == 1]
    
    def generate_legitimate_transactions(self, count: int = 1200) -> List[Dict]:
        """Generate normal transaction patterns."""
        print(f"Generating {count} legitimate transactions...")
        
        legitimate_users = [u["user_id"] for u in self.users if u["is_suspicious"] == 0]
        base_time = datetime.now() - timedelta(days=90)
        
        for _ in range(count):
            source = random.choice(legitimate_users)
            target = random.choice([u for u in legitimate_users if u != source])
            
            # Normal transaction amounts (log-normal distribution)
            amount = min(random.lognormvariate(6, 1.5), 50000)  # Most under $1000, some larger
            
            tx = {
                "transaction_id": self._generate_transaction_id(),
                "source_user_id": source,
                "target_user_id": target,
                "amount": round(amount, 2),
                "currency": random.choice(["USD", "USD", "USD", "EUR"]),
                "transaction_type": random.choice(self.TRANSACTION_TYPES),
                "timestamp": self._random_timestamp(base_time, datetime.now()),
                "is_international": 0,
                "source_country": "US",
                "target_country": "US",
                "description": random.choice([
                    "Payment for services", "Rent payment", "Invoice #" + str(random.randint(1000, 9999)),
                    "Monthly transfer", "Reimbursement", "Gift", "Loan repayment"
                ]),
                "is_suspicious": 0,
                "typology": None
            }
            self.transactions.append(tx)
            
        return self.transactions[-count:]
    
    def inject_smurfing_pattern(self) -> List[Dict]:
        """
        Typology A: Smurfing
        Multiple small deposits from different sources to a mule,
        followed by aggregated transfer to kingpin.
        """
        print("Injecting Smurfing patterns...")
        injected = []
        
        for mule_id in self.mules:
            kingpin_id = random.choice(self.kingpins)
            smurfs_subset = random.sample(self.smurfs, min(12, len(self.smurfs)))
            
            # All deposits happen within 1-2 hours
            base_time = datetime.now() - timedelta(days=random.randint(1, 30))
            
            total_deposited = 0
            deposit_txs = []
            
            for i, smurf_id in enumerate(smurfs_subset):
                # Small amounts under CTR threshold
                amount = random.uniform(500, 2500)
                total_deposited += amount
                
                tx = {
                    "transaction_id": self._generate_transaction_id(),
                    "source_user_id": smurf_id,
                    "target_user_id": mule_id,
                    "amount": round(amount, 2),
                    "currency": "USD",
                    "transaction_type": random.choice(["cash_deposit", "peer_to_peer", "ach_transfer"]),
                    "timestamp": base_time + timedelta(minutes=random.randint(0, 90)),
                    "is_international": 0,
                    "source_country": "US",
                    "target_country": "US",
                    "description": random.choice(["", "Payment", "Thanks", "For services"]),
                    "is_suspicious": 1,
                    "typology": "smurfing"
                }
                self.transactions.append(tx)
                deposit_txs.append(tx)
                injected.append(tx)
            
            # Aggregated transfer to kingpin (with small cut taken)
            aggregated_amount = total_deposited * random.uniform(0.92, 0.98)
            
            tx = {
                "transaction_id": self._generate_transaction_id(),
                "source_user_id": mule_id,
                "target_user_id": kingpin_id,
                "amount": round(aggregated_amount, 2),
                "currency": "USD",
                "transaction_type": random.choice(["wire_transfer", "crypto_buy", "international_wire"]),
                "timestamp": base_time + timedelta(hours=random.randint(2, 24)),
                "is_international": random.choice([0, 1]),
                "source_country": "US",
                "target_country": random.choice(["US", "MX", "PA"]),
                "description": "Business payment",
                "is_suspicious": 1,
                "typology": "smurfing"
            }
            self.transactions.append(tx)
            injected.append(tx)
            
        return injected
    
    def inject_structuring_pattern(self) -> List[Dict]:
        """
        Typology B: Structuring
        Repeated transactions just below reporting threshold.
        """
        print("Injecting Structuring patterns...")
        injected = []
        
        # Pair structurers together
        structurer_pairs = list(zip(self.structurers[::2], self.structurers[1::2]))
        
        for user_a, user_b in structurer_pairs:
            base_time = datetime.now() - timedelta(days=random.randint(1, 60))
            
            # Multiple back-and-forth transactions just under threshold
            for i in range(random.randint(5, 10)):
                amount = random.choice(self.STRUCTURING_AMOUNTS) + random.uniform(-100, 100)
                
                # A -> B
                tx1 = {
                    "transaction_id": self._generate_transaction_id(),
                    "source_user_id": user_a,
                    "target_user_id": user_b,
                    "amount": round(amount, 2),
                    "currency": "USD",
                    "transaction_type": random.choice(["wire_transfer", "ach_transfer", "check_deposit"]),
                    "timestamp": base_time + timedelta(days=i, hours=random.randint(0, 12)),
                    "is_international": 0,
                    "source_country": "US",
                    "target_country": "US",
                    "description": f"Invoice {random.randint(1000, 9999)}",
                    "is_suspicious": 1,
                    "typology": "structuring"
                }
                self.transactions.append(tx1)
                injected.append(tx1)
                
                # B -> A (slightly different amount)
                amount2 = random.choice(self.STRUCTURING_AMOUNTS) + random.uniform(-100, 100)
                tx2 = {
                    "transaction_id": self._generate_transaction_id(),
                    "source_user_id": user_b,
                    "target_user_id": user_a,
                    "amount": round(amount2, 2),
                    "currency": "USD",
                    "transaction_type": random.choice(["wire_transfer", "ach_transfer", "check_deposit"]),
                    "timestamp": base_time + timedelta(days=i, hours=random.randint(12, 23)),
                    "is_international": 0,
                    "source_country": "US",
                    "target_country": "US",
                    "description": f"Payment {random.randint(1000, 9999)}",
                    "is_suspicious": 1,
                    "typology": "structuring"
                }
                self.transactions.append(tx2)
                injected.append(tx2)
                
        return injected
    
    def inject_circular_flows(self) -> List[Dict]:
        """
        Typology C: Long Cycles (Layering)
        Complex rings of 5+ hops to obscure money trail.
        """
        print("Injecting Circular Flow patterns...")
        injected = []
        
        # Create multiple rings of different sizes
        ring_sizes = [5, 6, 7, 5, 6]
        
        available_members = self.ring_members.copy()
        random.shuffle(available_members)
        
        for ring_size in ring_sizes:
            if len(available_members) < ring_size:
                break
                
            ring = [available_members.pop() for _ in range(ring_size)]
            base_time = datetime.now() - timedelta(days=random.randint(5, 45))
            
            # Initial amount
            current_amount = random.uniform(50000, 200000)
            
            # Create the circular flow
            for i in range(len(ring)):
                source = ring[i]
                target = ring[(i + 1) % len(ring)]
                
                # Each hop loses 2-5% (fees, conversion costs)
                fee_rate = random.uniform(0.02, 0.05)
                current_amount = current_amount * (1 - fee_rate)
                
                tx = {
                    "transaction_id": self._generate_transaction_id(),
                    "source_user_id": source,
                    "target_user_id": target,
                    "amount": round(current_amount, 2),
                    "currency": random.choice(["USD", "EUR", "USD"]),
                    "transaction_type": random.choice(["wire_transfer", "international_wire", "crypto_buy"]),
                    "timestamp": base_time + timedelta(days=i, hours=random.randint(0, 23)),
                    "is_international": random.choice([0, 1]),
                    "source_country": random.choice(["US", "MX", "CA"]),
                    "target_country": random.choice(["US", "MX", "PA", "CA"]),
                    "description": random.choice(["Consulting fee", "Investment", "Trade settlement", "Commission"]),
                    "is_suspicious": 1,
                    "typology": "circular_flow"
                }
                self.transactions.append(tx)
                injected.append(tx)
                
        return injected
    
    def inject_rapid_movement(self) -> List[Dict]:
        """
        Additional Typology: Rapid Movement
        Funds received and immediately transferred out.
        """
        print("Injecting Rapid Movement patterns...")
        injected = []
        
        for mule_id in self.mules[:5]:
            base_time = datetime.now() - timedelta(days=random.randint(1, 20))
            
            # Legitimate-looking source
            legit_users = [u["user_id"] for u in self.users if u["is_suspicious"] == 0]
            source = random.choice(legit_users)
            kingpin = random.choice(self.kingpins)
            
            amount = random.uniform(15000, 75000)
            
            # Incoming transaction
            tx_in = {
                "transaction_id": self._generate_transaction_id(),
                "source_user_id": source,
                "target_user_id": mule_id,
                "amount": round(amount, 2),
                "currency": "USD",
                "transaction_type": "wire_transfer",
                "timestamp": base_time,
                "is_international": 0,
                "source_country": "US",
                "target_country": "US",
                "description": "Payment for goods",
                "is_suspicious": 1,
                "typology": "rapid_movement"
            }
            self.transactions.append(tx_in)
            injected.append(tx_in)
            
            # Immediate outgoing (within 30 minutes)
            tx_out = {
                "transaction_id": self._generate_transaction_id(),
                "source_user_id": mule_id,
                "target_user_id": kingpin,
                "amount": round(amount * 0.95, 2),
                "currency": "USD",
                "transaction_type": random.choice(["international_wire", "crypto_buy"]),
                "timestamp": base_time + timedelta(minutes=random.randint(5, 30)),
                "is_international": 1,
                "source_country": "US",
                "target_country": random.choice(["MX", "PA", "BZ"]),
                "description": "Transfer",
                "is_suspicious": 1,
                "typology": "rapid_movement"
            }
            self.transactions.append(tx_out)
            injected.append(tx_out)
            
        return injected
    
    def save_to_database(self):
        """Save all generated data to SQLite database."""
        print("Saving to database...")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Insert users
        for user in self.users:
            c.execute("""
                INSERT INTO users (user_id, name, risk_score, account_age_days, account_type,
                                   country, is_pep, kyc_verified, is_suspicious, typology)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user["user_id"], user["name"], user["risk_score"], user["account_age_days"],
                user["account_type"], user["country"], user["is_pep"], user["kyc_verified"],
                user["is_suspicious"], user["typology"]
            ))
        
        # Insert transactions
        for tx in self.transactions:
            c.execute("""
                INSERT INTO transactions (transaction_id, source_user_id, target_user_id, amount,
                                          currency, transaction_type, timestamp, is_international,
                                          source_country, target_country, description, is_suspicious, typology)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tx["transaction_id"], tx["source_user_id"], tx["target_user_id"], tx["amount"],
                tx["currency"], tx["transaction_type"], tx["timestamp"], tx["is_international"],
                tx["source_country"], tx["target_country"], tx["description"],
                tx["is_suspicious"], tx["typology"]
            ))
        
        # Insert typology labels
        for user in self.users:
            if user["typology"]:
                c.execute("""
                    INSERT INTO typology_labels (entity_type, entity_id, typology, description)
                    VALUES (?, ?, ?, ?)
                """, ("user", user["user_id"], user["typology"], f"User role: {user['typology']}"))
        
        for tx in self.transactions:
            if tx["typology"]:
                c.execute("""
                    INSERT INTO typology_labels (entity_type, entity_id, typology, description)
                    VALUES (?, ?, ?, ?)
                """, ("transaction", tx["transaction_id"], tx["typology"], f"Part of {tx['typology']} pattern"))
        
        conn.commit()
        conn.close()
        
    def generate_full_dataset(self):
        """Generate complete dataset with all patterns."""
        print("=" * 60)
        print("Financial Crime Data Generator")
        print("=" * 60)
        
        # Generate users
        self.generate_legitimate_users(400)
        self.generate_suspicious_users()
        
        # Generate transactions
        self.generate_legitimate_transactions(1200)
        smurfing_txs = self.inject_smurfing_pattern()
        structuring_txs = self.inject_structuring_pattern()
        circular_txs = self.inject_circular_flows()
        rapid_txs = self.inject_rapid_movement()
        
        # Save to database
        self.save_to_database()
        
        # Print summary
        print("\n" + "=" * 60)
        print("Generation Complete!")
        print("=" * 60)
        print(f"Total Users: {len(self.users)}")
        print(f"  - Legitimate: {len([u for u in self.users if u['is_suspicious'] == 0])}")
        print(f"  - Suspicious: {len([u for u in self.users if u['is_suspicious'] == 1])}")
        print(f"    - Kingpins: {len(self.kingpins)}")
        print(f"    - Mules: {len(self.mules)}")
        print(f"    - Smurfs: {len(self.smurfs)}")
        print(f"    - Structurers: {len(self.structurers)}")
        print(f"    - Ring Members: {len(self.ring_members)}")
        print(f"\nTotal Transactions: {len(self.transactions)}")
        print(f"  - Legitimate: {len([t for t in self.transactions if t['is_suspicious'] == 0])}")
        print(f"  - Suspicious: {len([t for t in self.transactions if t['is_suspicious'] == 1])}")
        print(f"    - Smurfing: {len(smurfing_txs)}")
        print(f"    - Structuring: {len(structuring_txs)}")
        print(f"    - Circular Flows: {len(circular_txs)}")
        print(f"    - Rapid Movement: {len(rapid_txs)}")
        print(f"\nDatabase saved to: {self.db_path}")
        
        return {
            "users": len(self.users),
            "transactions": len(self.transactions),
            "suspicious_users": len([u for u in self.users if u["is_suspicious"] == 1]),
            "suspicious_transactions": len([t for t in self.transactions if t["is_suspicious"] == 1])
        }


if __name__ == "__main__":
    generator = FinancialCrimeDataGenerator()
    generator.generate_full_dataset()
