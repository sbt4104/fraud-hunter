from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    SIGN_IN = "sign_in"
    ACCOUNT_LOOKUP = "account_lookup"
    TRANSACTION = "transaction"
    PASSWORD_RESET = "password_reset"

class AgentStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"

class Event(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: EventType
    account_id: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    risk_score: Optional[float] = 0.0
    event_data: Dict[str, Any] = Field(default_factory=dict)
    anomaly_flags: List[str] = Field(default_factory=list)
    source_system: str = "demo"

class Agent(BaseModel):
    agent_id: str
    name: str
    status: AgentStatus = AgentStatus.STOPPED
    account_ids: List[str] = Field(default_factory=list)
    events_processed: int = 0
    alerts_generated: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = None

class Analysis(BaseModel):
    analysis_id: str
    agent_id: str
    event_id: str
    timestamp: datetime
    risk_score: float
    fraud_indicators: List[str]
    reasoning: str
    recommended_actions: List[str]