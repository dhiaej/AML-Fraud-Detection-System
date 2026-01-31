import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent.parent
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "fraud_detection.db"))
    GNN_HIDDEN_CHANNELS = 16
    GNN_INPUT_FEATURES = 2

config = Config()
