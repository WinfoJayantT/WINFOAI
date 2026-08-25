from datetime import datetime

from pydantic import BaseModel


class TestScripts(BaseModel):
    test_script_id: str
    module_id: str
    test_case_number: str
    qualified_name: str
    script_name: str
    script_description: str
    objective: str
    agent_intent_name: str
    search_document: str
    search_vector: str
    script_type_code: str
    runtime_type_code: str
    estimated_duration_seconds: int
    display_sequence: int
    status_code: str
    version_no: int
    is_deleted: int
    deleted_date: datetime
    deleted_by: str
    creation_date: datetime
    created_by: str
    last_updated_date: datetime
    last_updated_by: str