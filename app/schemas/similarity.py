from typing import List, Optional

from pydantic import BaseModel


class SimilarityRequest(BaseModel):
    identifier: str
    limit: int = 5


class SimilarityMatch(BaseModel):
    test_script_number: Optional[str] = None
    script_name: str
    similarity_percentage: float
    matched_by_chunk: bool = False
    matched_chunk_attribution: Optional[str] = None


class SimilarityResponse(BaseModel):
    query_identifier: str
    matches: List[SimilarityMatch]
