from app.services.semantic_document_service import semantic_document_service

def test_valid_document_schema_check():
    good_doc = "### Process Area\n" * 1 + "business objective workflow input parameter validation " * 20
    assert semantic_document_service._is_valid_semantic_document(good_doc)
    assert not semantic_document_service._is_valid_semantic_document("too short")
