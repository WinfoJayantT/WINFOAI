import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConversationState(BaseModel):
    session_id: str = "default"
    last_user_query: str | None = None
    last_intent: str | None = None
    last_tool: str | None = None
    last_result_label: str | None = None
    last_result_script_ids: list[str] = Field(default_factory=list)
    can_execute_previous_result: bool = False


class ConversationStateService:
    def __init__(self):
        self._store: dict[str, ConversationState] = {}

    def get(self, session_id: str | None) -> ConversationState:
        sid = session_id or "default"
        if sid not in self._store:
            self._store[sid] = ConversationState(session_id=sid)
        return self._store[sid]

    def save(self, state: ConversationState) -> None:
        self._store[state.session_id] = state
        logger.info(
            f"Saved conversation state for session: {state.session_id} (tracked {len(state.last_result_script_ids)} script IDs)"
        )


conversation_state_service = ConversationStateService()
