from pydantic import BaseModel
from datetime import datetime

class TestScriptRoles(BaseModel):
    test_script_role_id: str
    test_script_id: str
    role_id: str
    creation_date: datetime
    created_by: str