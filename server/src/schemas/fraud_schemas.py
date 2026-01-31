from pydantic import BaseModel
from typing import List, Optional

class UserRiskResponse(BaseModel):
    user_id: str
    name: str
    risk_score: float
    account_age_days: int

class FraudDetectionResponse(BaseModel):
    user: UserRiskResponse
    neighborhood: List[UserRiskResponse]
    risk_probability: float

class FraudDetectionRequest(BaseModel):
    user_id: str
    depth: Optional[int] = 2  # Default depth for neighborhood search