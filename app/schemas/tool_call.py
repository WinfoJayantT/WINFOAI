from enum import Enum
from typing import Any

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
    arguments: dict[str, Any] = {}
    session_id: str | None = None


class ToolCallResult(BaseModel):
    status: ToolStatus
    tool: str
    message: str
    data: dict[str, Any] | None = None
    debug: dict[str, Any] | None = None
