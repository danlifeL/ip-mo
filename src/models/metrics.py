from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

class SSLStatus(BaseModel):
    valid: bool
    warning: bool = False
    expiry_date: Optional[datetime] = None

class Resources(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float

class MetricsResponse(BaseModel):
    timestamp: datetime
    response_time: float
    connection_count: int
    error_rate: float
    bandwidth: float
    ssl_status: SSLStatus
    resources: Resources

class MetricsHistoryResponse(MetricsResponse):
    pass 