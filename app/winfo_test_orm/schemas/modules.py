from datetime import datetime

from pydantic import BaseModel


class Modules(BaseModel):
    module_id: str
    process_area_id: str
    module_code: str
    module_name: str
    module_description: str
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