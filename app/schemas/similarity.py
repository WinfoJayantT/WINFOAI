
from pydantic import BaseModel


class SimilarityRequest(BaseModel):
    identifier: str
    limit: int = 5


class SimilarityMatch(BaseModel):
    test_script_number: str | None = None
    script_name: str
    similarity_percentage: float
    matched_by_chunk: bool = False
    matched_chunk_attribution: str | None = None


class SimilarityResponse(BaseModel):
    query_identifier: str
    matches: list[SimilarityMatch]
