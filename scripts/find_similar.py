#!/usr/bin/env python3
"""CLI entry point: python -m scripts.find_similar <identifier>"""
import sys

from app.services.similarity_service import similarity_service

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.find_similar <identifier>")
        sys.exit(1)
    result = similarity_service.find_similar(sys.argv[1])
    print(result)
