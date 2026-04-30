from typing import Optional
from fastapi import Header, HTTPException

from db import db


def require_user_id(x_user_id: Optional[str] = Header(default=None)) -> str:
    """Extract and validate the active user id from the X-User-ID request header."""
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=400, detail="X-User-ID header required")
    rows = db.query(
        "SELECT id FROM profiles WHERE id = ?" if db.driver == "sqlite"
        else "SELECT id FROM profiles WHERE id = :1",
        (x_user_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Profile {x_user_id} not found")
    return x_user_id
