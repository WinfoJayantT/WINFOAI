#!/usr/bin/env python3
"""CLI entry point: python -m scripts.group_scripts <module|process|process_area>"""
import sys

from app.schemas.grouping import GroupByField
from app.services.grouping_service import grouping_service

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.group_scripts <module|process|process_area>")
        sys.exit(1)
    result = grouping_service.group(GroupByField(sys.argv[1]))
    for key, scripts in result.get("groups", {}).items():
        print(f"{key}: {len(scripts)} script(s)")
