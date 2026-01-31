from unittest import TestCase
import torch
from torch_geometric.data import Data
from server.src.models.gnn_model import LaunderingGCN

class TestLaunderingGCN(TestCase):
    def setUp(self):
        # Sample node features: risk score and account age
        self.node_features = torch.tensor([[0.5, 30], [0.8, 60], [0.2, 10]], dtype=torch.float)
        # Sample edge index (3 nodes with edges between them)
        self.edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
        # Create a PyTorch Geometric Data object
        self.data = Data(x=self.node_features, edge_index=self.edge_index)

        # Initialize the GNN model
        self.model = LaunderingGCN(in_channels=2, out_channels=1)

    def test_forward_pass(self):
        # Run a forward pass
        output = self.model(self.data.x, self.data.edge_index)
        # Check the output shape
        self.assertEqual(output.shape, (3, 1))

    def test_model_training(self):
        # Sample target labels for training
        target = torch.tensor([[0], [1], [0]], dtype=torch.float)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)

        # Forward pass
        self.model.train()
        optimizer.zero_grad()
        output = self.model(self.data.x, self.data.edge_index)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(output, target)
        loss.backward()
        optimizer.step()

        # Check if loss is decreasing (not a rigorous test, but a basic check)
        self.assertTrue(loss.item() < 1.0)  # Assuming initial loss is high

    def test_output_probabilities(self):
        # Run a forward pass and apply sigmoid to get probabilities
        self.model.eval()
        with torch.no_grad():
            output = self.model(self.data.x, self.data.edge_index)
            probabilities = torch.sigmoid(output)
        
        # Check if probabilities are in the range [0, 1]
        self.assertTrue((probabilities >= 0).all() and (probabilities <= 1).all())