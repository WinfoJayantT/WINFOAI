#!/usr/bin/env python3
"""CLI entry point: python -m scripts.generate_semantic_document <identifier>"""
import sys

from app.repositories.step_repository import step_repository
from app.repositories.test_script_repository import test_script_repository
from app.services.semantic_document_service import semantic_document_service

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.generate_semantic_document <identifier>")
        sys.exit(1)
    identifier = sys.argv[1]
    script = test_script_repository.get_script_by_identifier(identifier)
    if script is None:
        print(f"No test script found for identifier '{identifier}'.")
        sys.exit(1)
    steps = step_repository.get_ordered_steps(script["id"])
    doc = semantic_document_service.generate_semantic_document(script, steps)
    print(doc)
