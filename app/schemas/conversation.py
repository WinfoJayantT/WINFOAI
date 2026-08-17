from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ConversationState(BaseModel):
    session_id: str
    last_user_query: Optional[str] = None
    last_intent: Optional[str] = None
    last_tool: Optional[str] = None
    last_result_label: Optional[str] = None
    last_result_script_ids: List[str] = []
    can_execute_previous_result: bool = False


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
