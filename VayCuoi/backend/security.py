
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = "khoa_bi_mat_cua_du_an"
ALGORITHM = "HS256"

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")
        role = payload.get("role")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Token không có thông tin người dùng."
            )

        return {
            "user_id": int(user_id),
            "role": role
        }

    except HTTPException:
        raise
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại."
        )


def require_admin(
    user: dict = Depends(get_current_user)
):
    if user["role"] != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền truy cập chức năng quản trị."
        )

    return user
