"""
Fraud Detection Service
Simplified version that works with existing infrastructure.
"""

import sqlite3
import torch
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from ..database.sqlite_connector import SQLiteConnector


@dataclass 
class ContributingFactor:
    factor_type: str
    description: str
    severity: str


class FraudService:
    """Fraud detection service using GNN."""
    
    def __init__(self, db: SQLiteConnector, gnn=None):
        self.db = db
        self.gnn = gnn
    
    def detect_fraud(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze a user for potential fraud.
        Returns risk score, explanation, and subgraph.
        """
        # Get user
        user = self.db.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get subgraph
        subgraph = self.db.get_user_subgraph(user_id, depth=2)
        
        # Calculate risk score using simple heuristics + network analysis
        risk_score = self._calculate_risk_score(user_id, user, subgraph)
        
        # Detect patterns
        patterns = self._detect_patterns(user_id, subgraph)
        
        # Build contributing factors
        factors = self._build_contributing_factors(user, patterns, risk_score)
        
        # Identify suspicious transactions
        suspicious_txs = self._identify_suspicious_transactions(user_id, subgraph)
        
        # Determine primary flag
        primary_flag = self._get_primary_flag(patterns)
        
        # Add predicted risk scores to nodes
        nodes_with_risk = []
        for node in subgraph.get("nodes", []):
            node_risk = self._calculate_node_risk(node, subgraph)
            nodes_with_risk.append({
                **node,
                "predicted_risk_score": node_risk
            })
        
        return {
            "user_id": user_id,
            "risk_probability": round(risk_score, 4),
            "risk_level": self._get_risk_level(risk_score),
            "primary_flag": primary_flag,
            "contributing_factors": [asdict(f) for f in factors],
            "suspicious_transactions": suspicious_txs,
            "subgraph": {
                "nodes": nodes_with_risk,
                "links": subgraph.get("links", [])
            }
        }
    
    def _calculate_risk_score(self, user_id: str, user: Dict, subgraph: Dict) -> float:
        """Calculate overall risk score using multiple signals."""
        base_risk = user.get("risk_score", 0.5)
        
        # Network-based risk
        nodes = subgraph.get("nodes", [])
        links = subgraph.get("links", [])
        
        # Factor 1: Neighbor risk (average risk of connected users)
        neighbor_risks = []
        for node in nodes:
            if node["user_id"] != user_id:
                neighbor_risks.append(node.get("risk_score", 0.5))
        avg_neighbor_risk = sum(neighbor_risks) / len(neighbor_risks) if neighbor_risks else 0.5
        
        # Factor 2: Transaction volume
        user_txs = [l for l in links if l["source"] == user_id or l["target"] == user_id]
        tx_count = len(user_txs)
        volume_risk = min(tx_count / 20.0, 1.0)  # Normalize
        
        # Factor 3: High-value transactions
        amounts = [l["amount"] for l in user_txs]
        max_amount = max(amounts) if amounts else 0
        high_value_risk = min(max_amount / 100000, 1.0)  # Normalize by 100k
        
        # Factor 4: Structuring detection (amounts near 10k)
        structuring_count = sum(1 for a in amounts if 9000 <= a <= 9999)
        structuring_risk = min(structuring_count / 3.0, 1.0)
        
        # Combine factors
        combined_risk = (
            base_risk * 0.3 +
            avg_neighbor_risk * 0.25 +
            volume_risk * 0.15 +
            high_value_risk * 0.15 +
            structuring_risk * 0.15
        )
        
        return min(max(combined_risk, 0.0), 1.0)
    
    def _calculate_node_risk(self, node: Dict, subgraph: Dict) -> float:
        """Calculate risk score for a single node."""
        base_risk = node.get("risk_score", 0.5)
        links = subgraph.get("links", [])
        
        # Get transactions involving this node
        user_id = node["user_id"]
        user_txs = [l for l in links if l["source"] == user_id or l["target"] == user_id]
        
        tx_factor = min(len(user_txs) / 10.0, 0.3)
        
        return min(base_risk + tx_factor, 1.0)
    
    def _detect_patterns(self, user_id: str, subgraph: Dict) -> Dict[str, Any]:
        """Detect money laundering patterns."""
        links = subgraph.get("links", [])
        
        patterns = {
            "smurfing": {"detected": False, "count": 0},
            "structuring": {"detected": False, "count": 0, "amounts": []},
            "circular_flow": {"detected": False, "depth": 0},
            "rapid_movement": {"detected": False, "count": 0},
            "high_velocity": {"detected": False, "count": 0}
        }
        
        # Get user's transactions
        incoming = [l for l in links if l["target"] == user_id]
        outgoing = [l for l in links if l["source"] == user_id]
        all_txs = incoming + outgoing
        
        # Smurfing: Many small incoming transactions
        small_incoming = [l for l in incoming if l["amount"] < 3000]
        if len(small_incoming) >= 5:
            patterns["smurfing"] = {
                "detected": True,
                "count": len(small_incoming),
                "total": sum(l["amount"] for l in small_incoming)
            }
        
        # Structuring: Amounts near reporting threshold
        structured = [l for l in all_txs if 9000 <= l["amount"] <= 9999]
        if len(structured) >= 2:
            patterns["structuring"] = {
                "detected": True,
                "count": len(structured),
                "amounts": [l["amount"] for l in structured]
            }
        
        # High velocity: Many transactions
        if len(all_txs) >= 10:
            patterns["high_velocity"] = {
                "detected": True,
                "count": len(all_txs)
            }
        
        # Check for circular flows (simplified)
        nodes = subgraph.get("nodes", [])
        adj = {}
        for link in links:
            src = link["source"]
            if src not in adj:
                adj[src] = set()
            adj[src].add(link["target"])
        
        # Simple cycle check
        def has_path(start, end, visited, depth=0):
            if depth > 5:
                return False
            if start == end and depth > 0:
                return True
            for neighbor in adj.get(start, []):
                if neighbor not in visited or neighbor == end:
                    if has_path(neighbor, end, visited | {neighbor}, depth + 1):
                        return True
            return False
        
        if has_path(user_id, user_id, set()):
            patterns["circular_flow"] = {"detected": True, "depth": 3}
        
        return patterns
    
    def _build_contributing_factors(self, user: Dict, patterns: Dict, 
                                    risk_score: float) -> List[ContributingFactor]:
        """Build list of contributing factors."""
        factors = []
        
        if risk_score > 0.7:
            factors.append(ContributingFactor(
                factor_type="high_risk",
                description="Overall risk score exceeds threshold",
                severity="high"
            ))
        
        if patterns["smurfing"]["detected"]:
            factors.append(ContributingFactor(
                factor_type="smurfing",
                description=f"Smurfing pattern: {patterns['smurfing']['count']} small deposits",
                severity="high"
            ))
        
        if patterns["structuring"]["detected"]:
            factors.append(ContributingFactor(
                factor_type="structuring", 
                description=f"Structuring: {patterns['structuring']['count']} transactions near $10,000",
                severity="high"
            ))
        
        if patterns["circular_flow"]["detected"]:
            factors.append(ContributingFactor(
                factor_type="circular_flow",
                description="Circular transaction flow detected",
                severity="critical"
            ))
        
        if patterns["high_velocity"]["detected"]:
            factors.append(ContributingFactor(
                factor_type="high_velocity",
                description=f"High transaction velocity: {patterns['high_velocity']['count']} transactions",
                severity="medium"
            ))
        
        if user.get("account_age_days", 365) < 90:
            factors.append(ContributingFactor(
                factor_type="new_account",
                description="Account is less than 90 days old",
                severity="low"
            ))
        
        return factors
    
    def _identify_suspicious_transactions(self, user_id: str, 
                                          subgraph: Dict) -> List[Dict]:
        """Identify suspicious transactions."""
        suspicious = []
        links = subgraph.get("links", [])
        
        for link in links:
            if link["source"] == user_id or link["target"] == user_id:
                reasons = []
                
                if 9000 <= link["amount"] <= 9999:
                    reasons.append("Amount near reporting threshold")
                
                if link["amount"] > 50000:
                    reasons.append("Large transaction amount")
                
                if link.get("transaction_type") in ["crypto_buy", "international_wire"]:
                    reasons.append("High-risk transaction type")
                
                if reasons:
                    suspicious.append({
                        "transaction_id": link.get("transaction_id", "unknown"),
                        "amount": link["amount"],
                        "source": link["source"],
                        "target": link["target"],
                        "reasons": reasons
                    })
        
        return suspicious[:10]
    
    def _get_primary_flag(self, patterns: Dict) -> Optional[str]:
        """Get the primary risk flag."""
        if patterns["circular_flow"]["detected"]:
            return "Circular Flow Detected"
        if patterns["smurfing"]["detected"]:
            return "Smurfing Detected"
        if patterns["structuring"]["detected"]:
            return "Structuring Detected"
        if patterns["high_velocity"]["detected"]:
            return "High Transaction Velocity"
        return None
    
    def _get_risk_level(self, score: float) -> str:
        """Get risk level string."""
        if score >= 0.8:
            return "critical"
        if score >= 0.6:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"
    
    def _detect_circular_path(self, user_id: str, transactions: List[Dict]) -> List[str]:
        """Detect circular transaction path starting from user_id."""
        # Build adjacency list
        adj = {}
        for tx in transactions:
            src = tx.get('source_user_id')
            tgt = tx.get('target_user_id')
            if src not in adj:
                adj[src] = []
            adj[src].append(tgt)
        
        # DFS to find cycle
        visited = set()
        path = []
        
        def dfs(current: str, start: str, depth: int = 0):
            if depth > 6:  # Max depth
                return None
            if current == start and depth > 0 and depth >= 3:
                return path + [current]
            
            visited.add(current)
            path.append(current)
            
            for neighbor in adj.get(current, []):
                if neighbor not in visited or neighbor == start:
                    result = dfs(neighbor, start, depth + 1)
                    if result:
                        return result
            
            path.pop()
            visited.remove(current)
            return None
        
        result = dfs(user_id, user_id, 0)
        return result if result else []