from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_connection
from schemas import UserRegister, UserLogin
from passlib.context import CryptContext
import jwt
import psycopg2
import psycopg2.extras
import psycopg2.errors
from datetime import datetime, timedelta

router = APIRouter()

SECRET_KEY = "khoa_bi_mat_cua_du_an"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schema cho API Quên mật khẩu
class PasswordReset(BaseModel):
    email: str
    new_password: str

@router.post("/api/register")
def register(user: UserRegister):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        hashed_password = pwd_context.hash(user.password)
        cur.execute(
            "INSERT INTO Users (full_name, email, phone, password_hash) VALUES (%s, %s, %s, %s) RETURNING id;",
            (user.full_name, user.email, user.phone, hashed_password)
        )
        new_user_id = cur.fetchone()[0]
        conn.commit()
        return {"message": "Đăng ký thành công!", "user_id": new_user_id}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Email hoặc SĐT đã tồn tại.")
    finally:
        cur.close()
        conn.close()

@router.post("/api/login")
def login(user: UserLogin):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM Users WHERE email = %s;", (user.email,))
        db_user = cur.fetchone()
        
        if not db_user or not pwd_context.verify(user.password, db_user['password_hash']):
            raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
            
        expire = datetime.utcnow() + timedelta(hours=24)
        token = jwt.encode({"user_id": db_user['id'], "role": db_user['role'], "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "message": "Đăng nhập thành công!", 
            "access_token": token, 
            "role": db_user['role'],
            "full_name": db_user['full_name'],
            "user_id": db_user['id'],        
            "name": db_user['full_name']
        }
    finally:
        cur.close()
        conn.close()

@router.put("/api/reset-password")
def reset_password(data: PasswordReset):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Kiểm tra email có tồn tại không
        cur.execute("SELECT id FROM Users WHERE email = %s;", (data.email,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống.")
            
        # Băm mật khẩu mới và lưu lại
        hashed_password = pwd_context.hash(data.new_password)
        cur.execute("UPDATE Users SET password_hash = %s WHERE email = %s;", (hashed_password, data.email))
        conn.commit()
        return {"message": "Đã đặt lại mật khẩu thành công!"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()