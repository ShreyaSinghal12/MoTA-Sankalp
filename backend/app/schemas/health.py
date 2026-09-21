from pydantic import BaseModel
from typing import Dict, Any

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    environment: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "database": "connected",
                "environment": {
                    "debug": True,
                    "log_level": "INFO"
                }
            }
        }
