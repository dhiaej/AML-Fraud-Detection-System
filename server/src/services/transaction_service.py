"""
Transaction Service with GNN Pre-Check and Structuring Detection
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from ..database.sqlite_connector import SQLiteConnector
from ..services.fraud_service import FraudService


class TransactionService:
    """Service for handling transactions with GNN fraud detection."""
    
    def __init__(self, db: SQLiteConnector, fraud_service: FraudService = None):
        self.db = db
        self.fraud_service = fraud_service or FraudService(db)
    
    def create_transaction(self, source_user_id: str, target_user_id: str,
                          amount: float, currency: str = "USD",
                          transaction_type: str = "transfer") -> Dict:
        """
        Create a transaction with GNN pre-check and structuring detection.
        Returns transaction info with status.
        """
        # Check if source user exists
        source_user = self.db.get_user_by_id(source_user_id)
        if not source_user:
            raise ValueError(f"Source user {source_user_id} not found")
        
        # Check if target user exists
        target_user = self.db.get_user_by_id(target_user_id)
        if not target_user:
            raise ValueError(f"Target user {target_user_id} not found")
        
        # Check if source user is frozen
        if source_user.get('status') == 'FROZEN':
            raise ValueError("Account is frozen. Cannot process transactions.")
        
        # Check if user has sufficient balance
        current_balance = source_user.get('balance', 0.0)
        if current_balance < amount:
            raise ValueError(f"Insufficient balance. Current balance: ${current_balance:.2f}")
        
        # Run GNN Pre-Check using fraud service
        try:
            fraud_result = self.fraud_service.detect_fraud(source_user_id)
            ai_risk_score = fraud_result.get('risk_probability', 0.5)
            typology = fraud_result.get('primary_flag', None)
        except Exception as e:
            # Fallback to basic risk score if GNN fails
            ai_risk_score = source_user.get('risk_score', 0.5)
            typology = None
        
        # Detect structuring: > 2 transactions between $9,000 and $10,000 in last 48 hours
        structuring_detected = self._detect_structuring(source_user_id, amount)
        
        # Check for high velocity (many transactions in short time)
        high_velocity = self._detect_high_velocity(source_user_id)
        
        # Determine if transaction should be flagged
        should_flag = (
            structuring_detected or
            high_velocity or
            (9000 <= amount <= 9999) or  # Amount near reporting threshold
            amount > 50000 or  # Large transaction
            ai_risk_score > 0.7  # High AI risk score
        )
        
        is_suspicious = 1 if should_flag else 0
        
        # Determine status
        if structuring_detected:
            status = 'BLOCKED'
            self.db.update_user_status(source_user_id, 'FROZEN')
        elif should_flag:
            status = 'FLAGGED'
        else:
            status = 'APPROVED'
        
        # Add transaction with AI risk score
        tx_id = self.db.add_transaction(
            source_user_id=source_user_id,
            target_user_id=target_user_id,
            amount=amount,
            currency=currency,
            transaction_type=transaction_type,
            status=status,
            is_suspicious=is_suspicious,
            ai_risk_score=ai_risk_score
        )
        
        # Deduct balance from source and add to target if transaction is approved
        if status == 'APPROVED':
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # Deduct from source
            source_balance = source_user.get('balance', 0.0)
            new_source_balance = source_balance - amount
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_source_balance, source_user_id))
            
            # Add to target
            target_balance = target_user.get('balance', 0.0)
            new_target_balance = target_balance + amount
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_target_balance, target_user_id))
            
            conn.commit()
            conn.close()
        
        return {
            "transaction_id": tx_id,
            "status": status,
            "source_user_id": source_user_id,
            "target_user_id": target_user_id,
            "amount": amount,
            "ai_risk_score": ai_risk_score,
            "typology": typology,
            "structuring_detected": structuring_detected,
            "account_frozen": structuring_detected,
            "new_balance": new_source_balance if status == 'APPROVED' else source_user.get('balance', 0.0),
            "message": "Account frozen due to structuring detection" if structuring_detected else 
                      ("Transaction flagged for compliance review" if should_flag else "Transaction approved")
        }
    
    def _detect_structuring(self, user_id: str, current_amount: float) -> bool:
        """
        Detect structuring: > 2 transactions between $9,000 and $10,000 in last 48 hours.
        Returns True if structuring is detected.
        """
        # Get transactions in last 48 hours
        recent_txs = self.db.get_user_transactions_in_window(user_id, hours=48)
        
        # Count transactions in structuring range (including current)
        structuring_count = sum(1 for tx in recent_txs 
                              if 9000 <= tx.get('amount', 0) <= 9999)
        
        # Add current transaction if it's in range
        if 9000 <= current_amount <= 9999:
            structuring_count += 1
        
        # Structuring detected if > 2 transactions in this range
        return structuring_count > 2
    
    def _detect_high_velocity(self, user_id: str) -> bool:
        """
        Detect high velocity: many transactions in short time.
        Returns True if high velocity is detected.
        """
        # Get transactions in last 24 hours
        recent_txs = self.db.get_user_transactions_in_window(user_id, hours=24)
        
        # High velocity if > 10 transactions in 24 hours
        return len(recent_txs) > 10
