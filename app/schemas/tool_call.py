from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ToolStatus(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_DATA = "insufficient_data"
    UNAUTHORIZED = "unauthorized"
    SERVICE_UNAVAILABLE = "service_unavailable"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"


class ToolCallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}
    session_id: Optional[str] = None


class ToolCallResult(BaseModel):
    status: ToolStatus
    tool: str
    message: str
    data: Optional[Dict[str, Any]] = None
    debug: Optional[Dict[str, Any]] = None
