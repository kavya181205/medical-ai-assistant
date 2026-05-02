from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.service.userService import UserService
from app.core.security.authhandler import AuthHandler
from app.schema.user import UserOutput

# 🔐 Security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db)
) -> UserOutput:

    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Authentication Credentials"
    )

    # 1. Extract token (NO need for "Bearer " parsing)
    token = credentials.credentials

    # 2. Decode JWT
    try:
        payload = AuthHandler.decode_jwt(token=token)
    except Exception:
        raise auth_exception

    # 3. Validate payload
    user_id = payload.get("user_id") if payload else None

    if not user_id:
        raise auth_exception

    # 4. Fetch user
    user = UserService(session=session).get_user_by_id(user_id=user_id)

    if not user:
        raise auth_exception

    return UserOutput(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email
    )