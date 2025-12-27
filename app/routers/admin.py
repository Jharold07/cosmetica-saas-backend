from fastapi import APIRouter, Depends
from app.core.dependencies import require_roles
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/ping")
def admin_ping(current_user: User = Depends(require_roles(["ADMIN"]))):
    return {"message": "Admin access granted"}
