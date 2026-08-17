from typing import List

from pydantic import BaseModel

from app.schemas.similarity import SimilarityMatch


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 10
    include_steps: bool = False


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SimilarityMatch]
