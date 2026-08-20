from pydantic import BaseModel
from datetime import datetime

class TestScriptReleases(BaseModel):
    test_script_release_id: str
    test_script_id: str
    application_release_id: str
    creation_date: datetime
    created_by: str