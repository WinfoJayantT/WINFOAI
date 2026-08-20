from pydantic import BaseModel
from datetime import datetime

class Streams(BaseModel):
    stream_id: str
    stream_code: str
    stream_name: str
    stream_description: str
    application_id: str
    runtime_type_code: str
    script_type_code: str
    status_code: str
    display_sequence: int
    version_no: int
    is_deleted: int
    deleted_date: datetime
    deleted_by: str
    creation_date: datetime
    created_by: str
    last_updated_date: datetime
    last_updated_by: str