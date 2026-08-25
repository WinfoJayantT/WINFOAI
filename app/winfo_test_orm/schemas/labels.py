from datetime import datetime

from pydantic import BaseModel


class Labels(BaseModel):
    label_id: str
    label_name: str
    status_code: str
    version_no: str
    is_deleted: int
    deleted_date: datetime
    deleted_by: str
    creation_date: datetime
    created_by: str
    last_updated_date: datetime
    last_updated_by: str