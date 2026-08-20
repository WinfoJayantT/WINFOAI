from pydantic import BaseModel
from datetime import datetime

class TestScriptProcesses(BaseModel):
    test_script_process_id: str
    test_script_id: str
    process_id: str
    creation_date: datetime
    created_by: str