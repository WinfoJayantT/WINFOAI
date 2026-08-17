from typing import List

from pydantic import BaseModel


class IndexingRequest(BaseModel):
    scope: str = "stale"  # "all" | "stale"


class IndexingResponse(BaseModel):
    scope: str
    indexed_script_ids: List[str]
    failed_script_ids: List[str]
