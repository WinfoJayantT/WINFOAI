from typing import Any

from pydantic import BaseModel


class ScriptLookupRequest(BaseModel):
    identifier: str


class TestScriptResponse(BaseModel):
    id: str
    test_script_number: str
    qualified_name: str | None = None
    script_name: str
    description: str | None = None
    objective: str | None = None
    module: str | None = None
    process: str | None = None
    process_area: str | None = None
    role: str | None = None
    steps: list[dict[str, Any]] = []
