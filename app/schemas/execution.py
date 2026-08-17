from typing import List

from pydantic import BaseModel


class ExecutionRequest(BaseModel):
    test_script_ids: List[str]


class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    test_script_ids: List[str]
