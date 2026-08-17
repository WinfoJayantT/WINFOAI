from typing import Any, Dict, Optional

from sqlalchemy import select

from app.models.orm import User
from app.repositories.db import get_session


class UserRepository:
    def resolve_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with get_session() as db:
            stmt = select(User).where(User.username.ilike(username))
            user = db.execute(stmt).scalar_one_or_none()
            if user is None:
                return None
            return {"id": user.id, "username": user.username, "display_name": user.display_name}


user_repository = UserRepository()
