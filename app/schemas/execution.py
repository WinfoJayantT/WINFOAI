
from pydantic import BaseModel


class ExecutionRequest(BaseModel):
    test_script_ids: list[str]


class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    test_script_ids: list[str]
