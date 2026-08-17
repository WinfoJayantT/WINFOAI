#!/usr/bin/env python3
"""CLI entry point: python -m scripts.semantic_search "<query>" """
import sys

from app.services.semantic_search_service import semantic_search_service

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python -m scripts.semantic_search "<query>"')
        sys.exit(1)
    for match in semantic_search_service.search(sys.argv[1]):
        print(match)
