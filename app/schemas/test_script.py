from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ScriptLookupRequest(BaseModel):
    identifier: str


class TestScriptResponse(BaseModel):
    id: str
    test_script_number: str
    qualified_name: Optional[str] = None
    script_name: str
    description: Optional[str] = None
    objective: Optional[str] = None
    module: Optional[str] = None
    process: Optional[str] = None
    process_area: Optional[str] = None
    role: Optional[str] = None
    steps: List[Dict[str, Any]] = []
