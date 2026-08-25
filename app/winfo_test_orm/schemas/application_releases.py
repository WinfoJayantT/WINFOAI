from datetime import datetime

from pydantic import BaseModel


class ApplicationReleases(BaseModel):
    application_release_id: str
    application_id: str
    release_code: str
    release_name: str
    release_start_date: datetime
    release_end_date: datetime
    release_notes: str
    status_code: str
    version_no: str
    is_deleted: int
    deleted_date: datetime
    deleted_by: str
    creation_date: datetime
    created_by: str
    last_updated_date: datetime
    last_updated_by: str