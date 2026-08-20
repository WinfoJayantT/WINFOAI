from pydantic import BaseModel


class RuntimeTypeMaster(BaseModel):
    runtime_type_code: str
    runtime_type_name: str