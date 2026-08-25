"""
User Repository
===============

This module handles querying the users table.
Used primarily to resolve AI command assignments and permissions based on Slack or UI usernames.

Key Responsibilities:
  1. Identity Resolution: Maps informal text usernames (e.g. from an LLM prompt) into
     formal database UUIDs and display names.
"""

from typing import Any

from sqlalchemy import select

from app.repositories.db import get_session
from app.winfo_test_orm.models.application_users import ApplicationUser


# ── class definition ──────────────────────────────────────────────────
class UserRepository:
    """
    Data Access Object (DAO) for resolving user identity in the AI context.
    """

    def resolve_by_username(self, username: str) -> dict[str, Any] | None:
        """
        Performs a case-insensitive lookup to find a user by their username handle.
        
        Args:
            username (str): The raw username token (e.g. "admin").
            
        Returns:
            Optional[Dict]: The hydrated user record payload, or None if unmatched.
        """
        with get_session() as db:
            stmt = select(ApplicationUser).where(ApplicationUser.email.ilike(username))
            user = db.execute(stmt).scalar_one_or_none()
            
            if user is None:
                return None
                
            return {
                "id": str(user.application_users_id), 
                "username": user.email, 
                "display_name": f"{user.first_name} {user.last_name}"
            }


# ── singleton export ──────────────────────────────────────────────────
user_repository = UserRepository()
