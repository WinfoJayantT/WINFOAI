#!/usr/bin/env python3
"""CLI entry point: python -m scripts.index_all_scripts"""
from app.services.indexing_service import indexing_service

if __name__ == "__main__":
    result = indexing_service.index_all()
    print(f"Indexed: {len(result['indexed_script_ids'])}")
    print(f"Failed:  {len(result['failed_script_ids'])}")
