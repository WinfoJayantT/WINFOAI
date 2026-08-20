from pydantic import BaseModel
from datetime import datetime

class Applications(BaseModel):
    application_id: str
    application_code: str
    application_name: str
    application_description: str
    vendor_name: str
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