"""
SQLite Database Connector for Money Laundering Detection
"""

import sqlite3
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime


class SQLiteConnector:
    """Database connector for fraud detection system."""
    
    def __init__(self, db_path: str = "data/fraud_detection.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Users table
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                risk_score REAL DEFAULT 0.5,
                account_age_days INTEGER DEFAULT 30,
                account_type TEXT DEFAULT 'personal',
                country TEXT DEFAULT 'US',
                is_pep INTEGER DEFAULT 0,
                kyc_verified INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_suspicious INTEGER DEFAULT 0,
                typology TEXT DEFAULT NULL,
                status TEXT DEFAULT 'ACTIVE',
                balance REAL DEFAULT 0.0
            )
        """)
        
        # Transactions table
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE,
                source_user_id TEXT NOT NULL,
                target_user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                transaction_type TEXT DEFAULT 'transfer',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'PENDING',
                is_international INTEGER DEFAULT 0,
                source_country TEXT DEFAULT 'US',
                target_country TEXT DEFAULT 'US',
                description TEXT,
                is_suspicious INTEGER DEFAULT 0,
                typology TEXT DEFAULT NULL,
                ai_risk_score REAL DEFAULT 0.0,
                FOREIGN KEY (source_user_id) REFERENCES users(user_id),
                FOREIGN KEY (target_user_id) REFERENCES users(user_id)
            )
        """)
        
        # Auth users table
        c.execute("""
            CREATE TABLE IF NOT EXISTS auth_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                user_id TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Appeals table
        c.execute("""
            CREATE TABLE IF NOT EXISTS appeals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                justification TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                reviewed_by TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Update users table to add status column
        try:
            c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # User methods
    def get_all_users(self) -> List[Dict]:
        """Get all users from database."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY risk_score DESC")
        users = [dict(row) for row in c.fetchall()]
        conn.close()
        return users
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get a specific user by ID."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def add_user(self, user_id: str, name: str, risk_score: float = 0.5, 
                 account_age_days: int = 30, balance: float = 0.0, 
                 status: str = 'ACTIVE', **kwargs) -> None:
        """Add a new user to the database."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO users (user_id, name, risk_score, account_age_days, balance, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, risk_score, account_age_days, balance, status))
        conn.commit()
        conn.close()
    
    # Transaction methods
    def get_all_transactions(self) -> List[Dict]:
        """Get all transactions."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        txs = [dict(row) for row in c.fetchall()]
        conn.close()
        return txs
    
    def add_transaction(self, source_user_id: str, target_user_id: str, 
                        amount: float, currency: str = "USD",
                        transaction_type: str = "transfer", status: str = "PENDING",
                        is_suspicious: int = 0, ai_risk_score: float = 0.0) -> str:
        """Add a new transaction. Returns transaction_id."""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Generate transaction ID
        c.execute("SELECT COUNT(*) FROM transactions")
        count = c.fetchone()[0]
        tx_id = f"TX{count + 1:06d}"
        
        c.execute("""
            INSERT INTO transactions (transaction_id, source_user_id, target_user_id, 
                                      amount, currency, transaction_type, timestamp, status,
                                      is_suspicious, ai_risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx_id, source_user_id, target_user_id, amount, currency, 
              transaction_type, datetime.now(), status, is_suspicious, ai_risk_score))
        conn.commit()
        conn.close()
        return tx_id
    
    def update_user_status(self, user_id: str, status: str) -> None:
        """Update user status (e.g., 'active', 'frozen')."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
        conn.commit()
        conn.close()
    
    def get_user_transactions_in_window(self, user_id: str, hours: int = 48) -> List[Dict]:
        """Get user transactions within a time window."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM transactions 
            WHERE (source_user_id = ? OR target_user_id = ?)
            AND timestamp >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp DESC
        """, (user_id, user_id, hours))
        txs = [dict(row) for row in c.fetchall()]
        conn.close()
        return txs
    
    def get_flagged_transactions(self) -> List[Dict]:
        """Get all transactions with FLAGGED status."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM transactions WHERE status = 'FLAGGED' ORDER BY timestamp DESC")
        txs = [dict(row) for row in c.fetchall()]
        conn.close()
        return txs
    
    # Authentication methods
    def create_auth_user(self, email: str, password_hash: str, user_id: str = None, role: str = "user") -> int:
        """Create an authentication user."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO auth_users (email, password_hash, user_id, role)
            VALUES (?, ?, ?, ?)
        """, (email, password_hash, user_id, role))
        conn.commit()
        user_auth_id = c.lastrowid
        conn.close()
        return user_auth_id
    
    def get_auth_user_by_email(self, email: str) -> Optional[Dict]:
        """Get auth user by email."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM auth_users WHERE email = ?", (email,))
        row = c.fetchone()
        conn.close()
        if row:
            return {key: row[key] for key in row.keys()}
        return None
    
    def get_auth_user_by_user_id(self, user_id: str) -> Optional[Dict]:
        """Get auth user by user_id."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM auth_users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_user_transactions(self, user_id: str) -> List[Dict]:
        """Get all transactions involving a user."""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM transactions 
            WHERE source_user_id = ? OR target_user_id = ?
            ORDER BY timestamp DESC
        """, (user_id, user_id))
        txs = [dict(row) for row in c.fetchall()]
        conn.close()
        return txs
    
    def get_user_subgraph(self, user_id: str, depth: int = 2) -> Dict:
        """Get the subgraph around a user up to specified depth."""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Collect nodes at each depth
        visited = {user_id}
        current_layer = {user_id}
        
        for _ in range(depth):
            next_layer = set()
            placeholders = ','.join('?' * len(current_layer))
            
            # Get neighbors
            c.execute(f"""
                SELECT DISTINCT target_user_id FROM transactions 
                WHERE source_user_id IN ({placeholders})
                UNION
                SELECT DISTINCT source_user_id FROM transactions 
                WHERE target_user_id IN ({placeholders})
            """, (*current_layer, *current_layer))
            
            for row in c.fetchall():
                neighbor = row[0]
                if neighbor not in visited:
                    next_layer.add(neighbor)
                    visited.add(neighbor)
            
            current_layer = next_layer
        
        # Get all nodes
        nodes = []
        for uid in visited:
            c.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
            row = c.fetchone()
            if row:
                nodes.append(dict(row))
        
        # Get all edges between visited nodes
        placeholders = ','.join('?' * len(visited))
        c.execute(f"""
            SELECT * FROM transactions 
            WHERE source_user_id IN ({placeholders}) 
            AND target_user_id IN ({placeholders})
        """, (*visited, *visited))
        
        links = []
        for row in c.fetchall():
            tx = dict(row)
            links.append({
                "source": tx["source_user_id"],
                "target": tx["target_user_id"],
                "amount": tx["amount"],
                "transaction_id": tx.get("transaction_id", tx.get("id")),
                "transaction_type": tx.get("transaction_type", "transfer")
            })
        
        conn.close()
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    def find_laundering_rings(self, max_depth: int = 6) -> List[Dict]:
        """Find circular transaction patterns using DFS."""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Build adjacency list
        c.execute("SELECT source_user_id, target_user_id, amount FROM transactions")
        adj = {}
        for row in c.fetchall():
            src, tgt, amount = row
            if src not in adj:
                adj[src] = []
            adj[src].append({"target": tgt, "amount": amount})
        
        # Get all users
        c.execute("SELECT user_id, name FROM users")
        user_names = {row[0]: row[1] for row in c.fetchall()}
        
        conn.close()
        
        # Find cycles using DFS
        rings = []
        
        def dfs(start: str, current: str, path: List[str], visited: set, depth: int):
            if depth > max_depth:
                return
            
            for edge in adj.get(current, []):
                neighbor = edge["target"]
                
                if neighbor == start and len(path) >= 3:
                    # Found a cycle
                    ring_path = []
                    for uid in path:
                        ring_path.append({
                            "user_id": uid,
                            "name": user_names.get(uid, uid)
                        })
                    
                    rings.append({
                        "path": ring_path,
                        "ring_length": len(path),
                        "transactions": []
                    })
                elif neighbor not in visited:
                    dfs(start, neighbor, path + [neighbor], visited | {neighbor}, depth + 1)
        
        # Start DFS from each node
        for start_node in list(adj.keys())[:50]:  # Limit to prevent long runtime
            dfs(start_node, start_node, [start_node], {start_node}, 0)
        
        # Remove duplicate rings
        seen = set()
        unique_rings = []
        for ring in rings:
            # Create a canonical form
            path_ids = tuple(sorted([p["user_id"] for p in ring["path"]]))
            if path_ids not in seen:
                seen.add(path_ids)
                unique_rings.append(ring)
        
        return unique_rings[:20]  # Return top 20 rings
    
    # Compatibility methods for seed script
    def create_user(self, user_id: str, name: str, risk_score: float = 0.5, 
                    account_age_days: int = 30) -> None:
        """Alias for add_user for compatibility."""
        self.add_user(user_id, name, risk_score, account_age_days)
    
    def create_transaction(self, source_user_id: str, target_user_id: str,
                          amount: float, currency: str = "USD",
                          transaction_type: str = "transfer") -> str:
        """Alias for add_transaction for compatibility."""
        return self.add_transaction(source_user_id, target_user_id, amount, currency, transaction_type, "SUCCESS")
    
    def get_high_risk_users(self, threshold: float = 0.7) -> List[Dict]:
        """Get users with risk score above threshold."""
        users = self.get_all_users()
        return [u for u in users if u.get('risk_score', 0) >= threshold]
    
    def close(self) -> None:
        """Close method for compatibility (no-op for SQLite)."""
        pass