from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from typing import List
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.models.role import Role


bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.execute(
        select(User).where(User.id == int(user_id), User.is_active == True)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

def require_roles(allowed_roles: List[str]):
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        # Obtenemos el nombre del rol desde DB para evitar problemas de lazy loading
        role_name = db.execute(
            select(Role.name).where(Role.id == current_user.role_id)
        ).scalar_one_or_none()

        if role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return checker

def require_super_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    role_name = db.execute(
        select(Role.name).where(
            Role.id == current_user.role_id,
            Role.tenant_id == current_user.tenant_id,
        )
    ).scalar_one_or_none()

    if role_name != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUPER_ADMIN privileges required",
        )

    return current_user