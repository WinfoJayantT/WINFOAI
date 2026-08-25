from datetime import datetime

from pydantic import BaseModel


class Roles(BaseModel):
    role_id: str
    role_code: str
    role_name: str
    role_description: str
    status_code: str
    version_no: str
    is_deleted: int
    deleted_date: datetime
    deleted_by: str
    creation_date: datetime
    created_by: str
    last_updated_date: datetime
    last_updated_by: str