
from pydantic import BaseModel


class ConversationState(BaseModel):
    session_id: str
    last_user_query: str | None = None
    last_intent: str | None = None
    last_tool: str | None = None
    last_result_label: str | None = None
    last_result_script_ids: list[str] = []
    can_execute_previous_result: bool = False


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
