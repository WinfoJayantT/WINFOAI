from datetime import datetime

from pydantic import BaseModel


class ProcessAreas(BaseModel):
    process_area_id: str
    stream_id: str
    process_area_code: str
    process_area_name: str
    process_area_description: str
    status_code: str
    display_sequence: int
    version_no: str
    is_deleted: int
    deleted_date: datetime
    deleted_by: str
    creation_date: datetime
    created_by: str
    last_updated_date: datetime
    last_updated_by: str