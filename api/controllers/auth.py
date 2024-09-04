from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import schema as s


def apple_auth(data: s.AppleAuth, db: Session) -> s.Token:
    """Logs in a user with Apple"""

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apple auth not implemented")
