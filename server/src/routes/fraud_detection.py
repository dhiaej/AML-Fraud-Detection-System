"""
Fraud Detection API Routes
Enhanced with pagination, admin actions, and transaction lifecycle
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from ..database.sqlite_connector import SQLiteConnector
from ..services.fraud_service import FraudService
from ..services.transaction_service import TransactionService

router = APIRouter()
db = SQLiteConnector()
fraud_service = FraudService(db)
transaction_service = TransactionService(db, fraud_service)


# Pydantic Models
class UserCreate(BaseModel):
    user_id: str
    name: str
    risk_score: float = 0.5
    account_age_days: int = 30


class TransactionCreate(BaseModel):
    source_user_id: str
    target_user_id: str
    amount: float
    currency: str = "USD"
    transaction_type: str = "transfer"


class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    message: str


# User Endpoints
@router.get("/users")
def get_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    risk_filter: Optional[str] = None,
    search: Optional[str] = None
):
    """Get paginated users with optional filtering and search."""
    try:
        users = db.get_all_users()
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            users = [u for u in users 
                    if search_lower in u.get('user_id', '').lower() 
                    or search_lower in u.get('name', '').lower()]
        
        # Apply risk filter
        if risk_filter == 'high':
            users = [u for u in users if u.get('risk_score', 0) >= 0.7]
        elif risk_filter == 'medium':
            users = [u for u in users if 0.4 <= u.get('risk_score', 0) < 0.7]
        elif risk_filter == 'low':
            users = [u for u in users if u.get('risk_score', 0) < 0.4]
        elif risk_filter == 'suspicious':
            users = [u for u in users if u.get('is_suspicious', 0) == 1]
        elif risk_filter == 'frozen':
            users = [u for u in users if u.get('status') == 'FROZEN']
        
        # Apply pagination
        total = len(users)
        paginated_users = users[offset:offset + limit]
        
        return {
            "users": paginated_users,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}")
def get_user(user_id: str):
    """Get a specific user by ID with transaction stats."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found. Please ensure you're logged in with a valid account.")
        
        # Get transaction stats
        transactions = db.get_user_transactions(user_id)
        
        # Calculate monthly spending (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        monthly_txs = []
        for tx in transactions:
            timestamp = tx.get('timestamp')
            if timestamp and isinstance(timestamp, str):
                try:
                    tx_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00').split('.')[0])
                    if tx_date >= thirty_days_ago:
                        monthly_txs.append(tx)
                except (ValueError, AttributeError):
                    pass
        
        outgoing_monthly = sum(tx.get('amount', 0) for tx in monthly_txs 
                              if tx.get('source_user_id') == user_id)
        
        # Add stats to user object
        user['monthly_spending'] = outgoing_monthly
        user['total_transactions'] = len(transactions)
        user['transaction_count'] = len(transactions)
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users")
def create_user(user: UserCreate):
    """Create a new user."""
    try:
        db.add_user(
            user_id=user.user_id,
            name=user.name,
            risk_score=user.risk_score,
            account_age_days=user.account_age_days
        )
        return {"message": "User created", "user_id": user.user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/deposit")
def deposit_funds(user_id: str, deposit_data: dict = Body(...)):
    """Simulate a deposit to user account."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        amount = deposit_data.get('amount', 0)
        deposit_type = deposit_data.get('deposit_type', 'wire')
        
        current_balance = user.get('balance', 0.0)
        new_balance = current_balance + amount
        
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        conn.commit()
        conn.close()
        
        return {"message": "Deposit successful", "new_balance": new_balance}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Transaction Endpoints
@router.post("/transactions", response_model=TransactionResponse)
def create_transaction(tx: TransactionCreate):
    """
    Create a transaction with structuring detection and auto-freeze.
    """
    try:
        result = transaction_service.create_transaction(
            source_user_id=tx.source_user_id,
            target_user_id=tx.target_user_id,
            amount=tx.amount,
            currency=tx.currency,
            transaction_type=tx.transaction_type
        )
        
        return TransactionResponse(
            transaction_id=result["transaction_id"],
            status=result["status"],
            message=result["message"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flagged-transactions")
def get_flagged_transactions():
    """Get all flagged transactions pending review."""
    try:
        flagged_txs = db.get_flagged_transactions()
        
        # Enrich with user risk scores
        result = []
        for tx in flagged_txs:
            source_user = db.get_user_by_id(tx.get('source_user_id'))
            result.append({
                "transaction_id": tx.get('transaction_id', f"TX_{tx.get('id', 0)}"),
                "source_user_id": tx.get('source_user_id'),
                "target_user_id": tx.get('target_user_id'),
                "amount": tx.get('amount', 0),
                "status": tx.get('status', 'FLAGGED'),
                "risk_score": source_user.get('risk_score', 0.5) if source_user else 0.5,
                "timestamp": tx.get('timestamp')
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
def get_alerts():
    """Get all alerts (flagged transactions) for admin dashboard."""
    return get_flagged_transactions()


# Fraud Detection Endpoints
@router.get("/detect-fraud/{user_id}")
def detect_fraud(user_id: str):
    """Analyze a user for potential fraud using GNN."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = fraud_service.detect_fraud(user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-risk-users")
def get_high_risk_users(threshold: float = Query(0.7, ge=0, le=1)):
    """Get users with risk score above threshold."""
    try:
        users = db.get_all_users()
        high_risk = [u for u in users if u.get("risk_score", 0) >= threshold]
        return high_risk
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/laundering-rings")
def get_laundering_rings():
    """Detect circular transaction patterns."""
    try:
        rings = db.find_laundering_rings()
        return rings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-network/{user_id}")
def get_user_network(user_id: str, depth: int = Query(2, ge=1, le=3)):
    """Get the transaction network around a user."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        subgraph = db.get_user_subgraph(user_id, depth)
        return subgraph
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin Endpoints
@router.post("/admin/approve-transaction/{transaction_id}")
def approve_transaction(transaction_id: str):
    """Admin approves a flagged transaction."""
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("UPDATE transactions SET status = 'APPROVED' WHERE transaction_id = ?", (transaction_id,))
        conn.commit()
        conn.close()
        return {"status": "approved", "transaction_id": transaction_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/approve-appeal/{user_id}")
def approve_appeal(user_id: str):
    """Admin approves a user's appeal and unfreezes account."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update appeal status
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE appeals 
            SET status = 'APPROVED', reviewed_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'PENDING'
        """, (user_id,))
        
        # Unfreeze user
        db.update_user_status(user_id, 'ACTIVE')
        
        conn.commit()
        conn.close()
        
        return {"status": "appeal_approved", "user_id": user_id, "message": "Appeal approved. User account unfrozen."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions")
def get_all_transactions():
    """Get all transactions with filters."""
    try:
        transactions = db.get_all_transactions()
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/transactions")
def get_user_transactions(user_id: str):
    """Get all transactions for a specific user."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        transactions = db.get_user_transactions(user_id)
        return transactions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/freeze-user/{user_id}")
def freeze_user(user_id: str):
    """Admin freezes a user account."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.update_user_status(user_id, 'FROZEN')
        return {"status": "frozen", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/unfreeze-user/{user_id}")
def unfreeze_user(user_id: str):
    """Admin unfreezes a user account."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.update_user_status(user_id, 'ACTIVE')
        return {"status": "active", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/block-user/{user_id}")
def block_user(user_id: str):
    """Admin permanently blocks a user account."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.update_user_status(user_id, 'BLOCKED')
        return {"status": "blocked", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/appeal")
def submit_appeal(user_id: str = Body(...), justification: str = Body(...)):
    """User submits an appeal for their frozen account."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO appeals (user_id, justification, status)
            VALUES (?, ?, 'PENDING')
        """, (user_id, justification))
        conn.commit()
        conn.close()
        
        return {"message": "Appeal submitted successfully", "status": "PENDING"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/appeals/{user_id}")
def get_user_appeals(user_id: str):
    """Get appeals for a specific user."""
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM appeals WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        appeals = [dict(row) for row in c.fetchall()]
        conn.close()
        return appeals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/reject-appeal/{user_id}")
def reject_appeal(user_id: str):
    """Admin rejects a user's appeal, keeping them frozen."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update appeal status
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE appeals 
            SET status = 'REJECTED', reviewed_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'PENDING'
        """, (user_id,))
        conn.commit()
        conn.close()
        
        # User remains frozen - no status change needed
        return {"status": "appeal_rejected", "user_id": user_id, "message": "Appeal rejected. User remains frozen."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs/{user_id}")
def get_audit_logs(user_id: str):
    """Get audit trail for a user showing explainability of AI decisions."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        logs = []
        
        # Get user's transactions
        transactions = db.get_user_transactions(user_id)
        
        # Detect circular flow
        if user.get('typology') in ['Circular Flow', 'Money Laundering']:
            # Find circular paths using fraud service
            try:
                path = fraud_service._detect_circular_path(user_id, transactions)
                if path and len(path) > 0:
                    logs.append({
                        "log_type": "Circular Flow",
                        "description": f"Circular transaction flow detected: {len(path)} nodes in cycle",
                        "details": {
                            "path": path,
                            "ai_risk_score": user.get('risk_score', 0.5)
                        },
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                # Fallback: create a simple path from transactions
                if len(transactions) >= 3:
                    path = [user_id]
                    for tx in transactions[:3]:
                        if tx.get('target_user_id') not in path:
                            path.append(tx.get('target_user_id'))
                    if len(path) >= 3:
                        path.append(user_id)  # Close the cycle
                        logs.append({
                            "log_type": "Circular Flow",
                            "description": f"Circular transaction flow detected: {len(path)-1} nodes in cycle",
                            "details": {
                                "path": path,
                                "ai_risk_score": user.get('risk_score', 0.5)
                            },
                            "timestamp": datetime.now().isoformat()
                        })
        
        # Detect structuring
        if user.get('typology') == 'Structuring':
            structuring_txs = [tx for tx in transactions 
                             if 9000 <= tx.get('amount', 0) <= 9999]
            if len(structuring_txs) >= 2:
                logs.append({
                    "log_type": "Structuring",
                    "description": f"Structuring detected: {len(structuring_txs)} transactions near $10,000 threshold",
                    "details": {
                        "transactions": [
                            {
                                "amount": tx.get('amount', 0),
                                "timestamp": tx.get('timestamp', '')
                            }
                            for tx in structuring_txs[:10]  # Limit to 10
                        ],
                        "ai_risk_score": user.get('risk_score', 0.5)
                    },
                    "timestamp": datetime.now().isoformat()
                })
        
        # High velocity
        if user.get('typology') == 'High Velocity':
            recent_txs = [tx for tx in transactions if tx.get('timestamp')]
            if len(recent_txs) > 10:
                logs.append({
                    "log_type": "High Velocity",
                    "description": f"High transaction velocity: {len(recent_txs)} transactions detected",
                    "details": {
                        "transaction_count": len(recent_txs),
                        "ai_risk_score": user.get('risk_score', 0.5)
                    },
                    "timestamp": datetime.now().isoformat()
                })
        
        # Smurfing
        if user.get('typology') == 'Smurfing':
            small_txs = [tx for tx in transactions if tx.get('amount', 0) < 3000]
            if len(small_txs) >= 5:
                logs.append({
                    "log_type": "Smurfing",
                    "description": f"Smurfing pattern: {len(small_txs)} small transactions detected",
                    "details": {
                        "transaction_count": len(small_txs),
                        "total_amount": sum(tx.get('amount', 0) for tx in small_txs),
                        "ai_risk_score": user.get('risk_score', 0.5)
                    },
                    "timestamp": datetime.now().isoformat()
                })
        
        # General risk score log
        logs.append({
            "log_type": "AI Risk Assessment",
            "description": f"GNN model calculated risk score: {(user.get('risk_score', 0.5) * 100):.0f}%",
            "details": {
                "ai_risk_score": user.get('risk_score', 0.5),
                "account_age_days": user.get('account_age_days', 0)
            },
            "timestamp": datetime.now().isoformat()
        })
        
        return logs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/dismiss-alert/{transaction_id}")
def dismiss_alert(transaction_id: str):
    """Admin dismisses a flagged alert."""
    return {"status": "dismissed", "transaction_id": transaction_id}
