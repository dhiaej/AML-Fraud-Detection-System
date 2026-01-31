from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.fraud_detection import router as fraud_detection_router
from .routes.auth import router as auth_router
from .config import config

app = FastAPI(
    title="Money Laundering Detection API",
    description="Detect circular transaction flows using Graph Neural Networks and SQLite",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(fraud_detection_router, prefix="/api/v1", tags=["Fraud Detection"])

@app.get("/")
def read_root():
    return {"name": "Money Laundering Detection API", "version": "1.0.0", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "SQLite"}
