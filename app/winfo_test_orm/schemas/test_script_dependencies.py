from datetime import datetime

from pydantic import BaseModel


class TestScriptDependencies(BaseModel):
    test_script_dependency_id: str
    test_script_id: str
    depends_on_test_script_id: str
    creation_date: datetime
    created_by: str
    last_updated_date: datetime
    last_updated_by: str