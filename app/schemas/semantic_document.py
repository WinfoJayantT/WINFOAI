from pydantic import BaseModel


class SemanticDocumentRequest(BaseModel):
    identifier: str


class SemanticDocumentResponse(BaseModel):
    test_script_id: str
    semantic_document: str
    generated_by: str  # 'llm' | 'deterministic_fallback'
