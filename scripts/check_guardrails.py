#!/usr/bin/env python3
"""
Guardrail scanner referenced in PROJECT_CONTEXT_FINAL.md sections 22 and 30.
Fails (non-zero exit) if banned patterns are found in production code under app/.
Run manually: python scripts/check_guardrails.py
Or wire into pre-commit (see README).
"""

import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"

# (pattern, human-readable reason)
BANNED_PATTERNS = [
    (r'\bCANONICAL_ERP_SCHEMAS\b', "hardcoded canonical ERP schema dict"),
    (r'\bCANONICAL_ERP_STEPS\b', "hardcoded canonical ERP steps dict"),
    (r'if\s+["\']supplier["\']\s+in', "keyword-based supplier routing"),
    (r'if\s+["\']invoice["\']\s+in', "keyword-based invoice routing"),
    (r'if\s+["\']employee["\']\s+in', "keyword-based employee routing"),
    (r'if\s+["\']payroll["\']\s+in', "keyword-based payroll routing"),
    (r'return\s+all_scripts\b', "silent fallback returning all scripts"),
    (r'session\s*=\s*sessionmaker', "direct SQLAlchemy session creation outside repositories/db.py"),
]

# Files allowed to reference sessionmaker etc.
ALLOWLIST = {APP_DIR / "repositories" / "db.py"}


def scan() -> list[str]:
    violations = []
    for path in APP_DIR.rglob("*.py"):
        if path in ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern, reason in BANNED_PATTERNS:
            if re.search(pattern, text):
                violations.append(f"{path.relative_to(APP_DIR.parent)}: {reason} (pattern: {pattern})")
    return violations


def main() -> int:
    violations = scan()
    if violations:
        print("Guardrail violations found:\n")
        for v in violations:
            print(f"  - {v}")
        print(f"\n{len(violations)} violation(s). See PROJECT_CONTEXT_FINAL.md sections 10, 22, 23.")
        return 1
    print("No guardrail violations found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
