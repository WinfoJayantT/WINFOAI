from datetime import datetime

from pydantic import BaseModel


class TestScriptLabels(BaseModel):
    test_script_label_id: str
    test_script_id: str
    label_id: str
    creation_date: datetime
    created_by: str