"""
Graph Attention Network (GAT) for Money Laundering Detection

This module implements a GATv2-based architecture that:
1. Learns attention weights based on edge attributes (amount, time)
2. Captures complex transaction patterns
3. Returns explainable attention scores
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict
import math


class EdgeAttnGATConv(nn.Module):
    """
    Graph Attention Convolution with Edge Attributes.
    
    Unlike standard GAT which only uses node features for attention,
    this layer incorporates edge attributes (transaction amount, time delta)
    into the attention mechanism.
    """
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        edge_dim: int = 2,
        heads: int = 4,
        concat: bool = True,
        dropout: float = 0.2,
        negative_slope: float = 0.2
    ):
        super().__init__()
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.edge_dim = edge_dim
        self.heads = heads
        self.concat = concat
        self.dropout = dropout
        self.negative_slope = negative_slope
        
        # Linear transformations for node features
        self.lin_src = nn.Linear(in_channels, heads * out_channels, bias=False)
        self.lin_dst = nn.Linear(in_channels, heads * out_channels, bias=False)
        
        # Edge attribute transformation
        self.lin_edge = nn.Linear(edge_dim, heads * out_channels, bias=False)
        
        # Attention parameters (GATv2 style - applies attention after concat)
        self.att = nn.Parameter(torch.Tensor(1, heads, out_channels))
        
        # Bias
        if concat:
            self.bias = nn.Parameter(torch.Tensor(heads * out_channels))
        else:
            self.bias = nn.Parameter(torch.Tensor(out_channels))
            
        self._reset_parameters()
        
    def _reset_parameters(self):
        nn.init.xavier_uniform_(self.lin_src.weight)
        nn.init.xavier_uniform_(self.lin_dst.weight)
        nn.init.xavier_uniform_(self.lin_edge.weight)
        nn.init.xavier_uniform_(self.att)
        nn.init.zeros_(self.bias)
        
    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: Optional[torch.Tensor] = None,
        return_attention_weights: bool = False
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass with optional attention weight return.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge attributes [num_edges, edge_dim]
            return_attention_weights: Whether to return attention weights
            
        Returns:
            out: Updated node features
            attention_weights: (edge_index, attention) if requested
        """
        num_nodes = x.size(0)
        num_edges = edge_index.size(1) if edge_index.numel() > 0 else 0
        
        # Handle empty graph
        if num_edges == 0:
            out = self.lin_src(x)
            if not self.concat:
                out = out.view(-1, self.heads, self.out_channels).mean(dim=1)
            out = out + self.bias
            if return_attention_weights:
                return out, (edge_index, torch.tensor([]))
            return out
        
        # Transform node features
        x_src = self.lin_src(x).view(-1, self.heads, self.out_channels)
        x_dst = self.lin_dst(x).view(-1, self.heads, self.out_channels)
        
        # Get source and target node features for each edge
        row, col = edge_index[0], edge_index[1]
        x_i = x_src[row]  # Source nodes [num_edges, heads, out_channels]
        x_j = x_dst[col]  # Target nodes [num_edges, heads, out_channels]
        
        # Include edge attributes if provided
        if edge_attr is not None:
            edge_feat = self.lin_edge(edge_attr).view(-1, self.heads, self.out_channels)
            # GATv2: attention on transformed and combined features
            alpha_input = F.leaky_relu(x_i + x_j + edge_feat, self.negative_slope)
        else:
            alpha_input = F.leaky_relu(x_i + x_j, self.negative_slope)
        
        # Compute attention scores
        alpha = (alpha_input * self.att).sum(dim=-1)  # [num_edges, heads]
        
        # Softmax over incoming edges for each node
        alpha = self._softmax(alpha, col, num_nodes)
        alpha = F.dropout(alpha, p=self.dropout, training=self.training)
        
        # Aggregate messages
        out = torch.zeros(num_nodes, self.heads, self.out_channels, device=x.device)
        
        # Message passing: weighted sum of neighbor features
        msg = x_j * alpha.unsqueeze(-1)
        out.scatter_add_(0, col.view(-1, 1, 1).expand(-1, self.heads, self.out_channels), msg)
        
        # Concat or average heads
        if self.concat:
            out = out.view(-1, self.heads * self.out_channels)
        else:
            out = out.mean(dim=1)
            
        out = out + self.bias
        
        if return_attention_weights:
            return out, (edge_index, alpha)
        return out
    
    def _softmax(self, alpha: torch.Tensor, index: torch.Tensor, num_nodes: int) -> torch.Tensor:
        """Compute softmax over edges for each target node."""
        # Numerical stability
        alpha_max = torch.zeros(num_nodes, alpha.size(1), device=alpha.device)
        alpha_max.scatter_reduce_(0, index.view(-1, 1).expand(-1, alpha.size(1)), alpha, reduce='amax')
        alpha = alpha - alpha_max[index]
        
        # Exp and sum
        alpha = alpha.exp()
        alpha_sum = torch.zeros(num_nodes, alpha.size(1), device=alpha.device)
        alpha_sum.scatter_add_(0, index.view(-1, 1).expand(-1, alpha.size(1)), alpha)
        
        # Normalize
        return alpha / (alpha_sum[index] + 1e-16)


class LaunderingGATv2(nn.Module):
    """
    Graph Attention Network for Money Laundering Detection.
    
    Architecture:
    - 2 GAT layers with edge attribute attention
    - Skip connections for gradient flow
    - Multi-head attention for capturing different patterns
    - Returns both risk scores and attention weights for explainability
    
    Features:
    - Node features: [risk_score, account_age, in_degree, out_degree, ...]
    - Edge features: [amount_normalized, time_delta, is_international, ...]
    """
    
    def __init__(
        self,
        node_features: int = 6,
        edge_features: int = 4,
        hidden_channels: int = 32,
        num_heads: int = 4,
        num_classes: int = 1,
        dropout: float = 0.3
    ):
        super().__init__()
        
        self.node_features = node_features
        self.edge_features = edge_features
        self.hidden_channels = hidden_channels
        self.num_heads = num_heads
        self.dropout = dropout
        
        # Input projection
        self.input_proj = nn.Linear(node_features, hidden_channels)
        
        # GAT layers
        self.conv1 = EdgeAttnGATConv(
            in_channels=hidden_channels,
            out_channels=hidden_channels,
            edge_dim=edge_features,
            heads=num_heads,
            concat=True,
            dropout=dropout
        )
        
        self.conv2 = EdgeAttnGATConv(
            in_channels=hidden_channels * num_heads,
            out_channels=hidden_channels,
            edge_dim=edge_features,
            heads=num_heads,
            concat=False,  # Average heads in final layer
            dropout=dropout
        )
        
        # Skip connection projection
        self.skip_proj = nn.Linear(hidden_channels, hidden_channels)
        
        # Batch normalization
        self.bn1 = nn.BatchNorm1d(hidden_channels * num_heads)
        self.bn2 = nn.BatchNorm1d(hidden_channels)
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels // 2, num_classes)
        )
        
        # Store attention weights for explainability
        self.attention_weights_layer1 = None
        self.attention_weights_layer2 = None
        
    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: Optional[torch.Tensor] = None,
        return_attention: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, node_features]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge attributes [num_edges, edge_features]
            return_attention: Whether to return attention weights
            
        Returns:
            Dictionary containing:
            - risk_scores: Predicted risk probabilities [num_nodes, 1]
            - attention_weights: List of attention tensors (if requested)
            - node_embeddings: Hidden representations [num_nodes, hidden_channels]
        """
        # Input projection
        x = self.input_proj(x)
        x_skip = self.skip_proj(x)
        
        # First GAT layer
        x, attn1 = self.conv1(x, edge_index, edge_attr, return_attention_weights=True)
        x = self.bn1(x)
        x = F.elu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        self.attention_weights_layer1 = attn1
        
        # Second GAT layer
        x, attn2 = self.conv2(x, edge_index, edge_attr, return_attention_weights=True)
        x = self.bn2(x)
        x = F.elu(x)
        
        self.attention_weights_layer2 = attn2
        
        # Skip connection
        x = x + x_skip
        
        # Store embeddings before classification
        node_embeddings = x.clone()
        
        # Classification
        logits = self.classifier(x)
        risk_scores = torch.sigmoid(logits)
        
        result = {
            "risk_scores": risk_scores,
            "logits": logits,
            "node_embeddings": node_embeddings
        }
        
        if return_attention:
            result["attention_weights"] = [
                self.attention_weights_layer1,
                self.attention_weights_layer2
            ]
            
        return result
    
    def get_attention_for_edges(self) -> Optional[torch.Tensor]:
        """
        Get aggregated attention weights for each edge.
        Useful for visualizing which transactions are most important.
        """
        if self.attention_weights_layer2 is None:
            return None
            
        edge_index, alpha = self.attention_weights_layer2
        # Average attention across heads
        return alpha.mean(dim=1)
    
    def predict_with_explanation(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Make predictions with full explainability output.
        """
        self.eval()
        with torch.no_grad():
            result = self.forward(x, edge_index, edge_attr, return_attention=True)
            
            # Get edge importance scores
            edge_importance = self.get_attention_for_edges()
            
            result["edge_importance"] = edge_importance
            
        return result


class LaunderingGCN(nn.Module):
    """
    Backward-compatible GCN model.
    Wraps the new GAT model for compatibility with existing code.
    """
    
    def __init__(
        self,
        in_channels: int = 2,
        hidden_channels: int = 16,
        out_channels: int = 1
    ):
        super().__init__()
        
        # Map old parameters to new model
        self.gat = LaunderingGATv2(
            node_features=in_channels,
            edge_features=4,
            hidden_channels=hidden_channels,
            num_heads=4,
            num_classes=out_channels
        )
        
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Legacy forward method."""
        result = self.gat(x, edge_index, edge_attr=None, return_attention=False)
        return result["logits"]
    
    def predict_proba(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Legacy prediction method."""
        result = self.gat(x, edge_index, edge_attr=None, return_attention=False)
        return result["risk_scores"]


# Feature extraction utilities
class FeatureExtractor:
    """
    Extracts node and edge features from raw transaction data.
    """
    
    @staticmethod
    def extract_node_features(user_data: Dict) -> torch.Tensor:
        """
        Extract features for a single node.
        
        Features:
        - risk_score: Base risk score [0, 1]
        - account_age_norm: Normalized account age [0, 1]
        - is_pep: Politically exposed person flag
        - kyc_verified: KYC verification status
        - in_degree_norm: Normalized in-degree
        - out_degree_norm: Normalized out-degree
        """
        features = [
            user_data.get("risk_score", 0.5),
            min(user_data.get("account_age_days", 0) / 3650.0, 1.0),
            float(user_data.get("is_pep", 0)),
            float(user_data.get("kyc_verified", 1)),
            min(user_data.get("in_degree", 0) / 100.0, 1.0),
            min(user_data.get("out_degree", 0) / 100.0, 1.0)
        ]
        return torch.tensor(features, dtype=torch.float32)
    
    @staticmethod
    def extract_edge_features(transaction_data: Dict, max_amount: float = 1000000) -> torch.Tensor:
        """
        Extract features for a single edge.
        
        Features:
        - amount_norm: Normalized transaction amount [0, 1]
        - is_international: International transaction flag
        - time_delta_norm: Normalized time since account creation
        - is_high_risk_type: Whether transaction type is high risk
        """
        high_risk_types = ["crypto_buy", "crypto_sell", "international_wire", "cash_deposit"]
        
        features = [
            min(transaction_data.get("amount", 0) / max_amount, 1.0),
            float(transaction_data.get("is_international", 0)),
            min(transaction_data.get("time_delta_hours", 0) / 8760.0, 1.0),  # Normalize by 1 year
            float(transaction_data.get("transaction_type", "") in high_risk_types)
        ]
        return torch.tensor(features, dtype=torch.float32)


if __name__ == "__main__":
    # Test the model
    print("Testing LaunderingGATv2...")
    
    # Create sample data
    num_nodes = 10
    num_edges = 20
    
    x = torch.randn(num_nodes, 6)  # 6 node features
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    edge_attr = torch.randn(num_edges, 4)  # 4 edge features
    
    # Initialize model
    model = LaunderingGATv2(
        node_features=6,
        edge_features=4,
        hidden_channels=32,
        num_heads=4
    )
    
    # Forward pass
    result = model(x, edge_index, edge_attr, return_attention=True)
    
    print(f"Risk scores shape: {result['risk_scores'].shape}")
    print(f"Node embeddings shape: {result['node_embeddings'].shape}")
    print(f"Number of attention layers: {len(result['attention_weights'])}")
    
    # Test backward compatibility
    print("\nTesting backward compatibility...")
    old_model = LaunderingGCN(in_channels=2, hidden_channels=16)
    x_old = torch.randn(num_nodes, 2)
    proba = old_model.predict_proba(x_old, edge_index)
    print(f"Legacy prediction shape: {proba.shape}")
    
    print("\nAll tests passed!")
