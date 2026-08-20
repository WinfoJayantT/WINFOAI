from pydantic import BaseModel


class StatusMaster(BaseModel):
    status_code: str
    status_name: str