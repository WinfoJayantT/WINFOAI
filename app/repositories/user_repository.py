"""
User Repository
===============

This module handles querying the users table.
Used primarily to resolve AI command assignments and permissions based on Slack or UI usernames.

Key Responsibilities:
  1. Identity Resolution: Maps informal text usernames (e.g. from an LLM prompt) into
     formal database UUIDs and display names.
"""

from typing import Any, Dict, Optional
from sqlalchemy import select

from app.models.orm import User
from app.repositories.db import get_session


# ── class definition ──────────────────────────────────────────────────
class UserRepository:
    """
    Data Access Object (DAO) for resolving user identity in the AI context.
    """

    def resolve_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Performs a case-insensitive lookup to find a user by their username handle.
        
        Args:
            username (str): The raw username token (e.g. "admin").
            
        Returns:
            Optional[Dict]: The hydrated user record payload, or None if unmatched.
        """
        with get_session() as db:
            stmt = select(User).where(User.username.ilike(username))
            user = db.execute(stmt).scalar_one_or_none()
            
            if user is None:
                return None
                
            return {
                "id": user.id, 
                "username": user.username, 
                "display_name": user.display_name
            }


# ── singleton export ──────────────────────────────────────────────────
user_repository = UserRepository()
