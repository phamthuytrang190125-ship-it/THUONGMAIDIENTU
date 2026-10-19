from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, date

app = FastAPI()

# --- 1. CẤU HÌNH DATABASE ---
DB_HOST = "localhost"
DB_NAME = "wedding_dress_rental"
DB_USER = "postgres" 
DB_PASS = "123456" # Đảm bảo đúng mật khẩu pgAdmin của bạn

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

# --- 2. CẤU HÌNH BẢO MẬT ---
SECRET_KEY = "khoa_bi_mat_cua_du_an" # Dùng để ký bảo mật JWT Token
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # Công cụ mã hóa password

# --- 3. ĐỊNH NGHĨA DỮ LIỆU ĐẦU VÀO (PYDANTIC) ---
class UserRegister(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# --- 4. CÁC API GỐC ---
@app.get("/")
def home():
    return {"message": "Chào mừng đến với Hệ thống cho thuê Váy Cưới MVP!"}

@app.get("/api/dresses")
def get_dresses():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) 
        cur.execute('SELECT * FROM Dresses;')
        dresses = cur.fetchall()
        cur.close()
        conn.close()
        return dresses
    except Exception as e:
        return {"error": str(e)}

# --- 5. API ĐĂNG KÝ (REGISTER) ---
@app.post("/api/register")
def register(user: UserRegister):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Băm (Hash) mật khẩu trước khi lưu
        hashed_password = pwd_context.hash(user.password)
        
        # Lưu vào database, mặc định role là CUSTOMER (đã set trong SQL)
        cur.execute(
            "INSERT INTO Users (full_name, email, phone, password_hash) VALUES (%s, %s, %s, %s) RETURNING id;",
            (user.full_name, user.email, user.phone, hashed_password)
        )
        new_user_id = cur.fetchone()[0]
        conn.commit()
        return {"message": "Đăng ký thành công!", "user_id": new_user_id}
    
    except psycopg2.errors.UniqueViolation:
        conn.rollback() # Hoàn tác nếu email/sđt bị trùng
        raise HTTPException(status_code=400, detail="Email hoặc số điện thoại đã tồn tại.")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# --- 6. API ĐĂNG NHẬP (LOGIN) ---
@app.post("/api/login")
def login(user: UserLogin):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Tìm user theo email
        cur.execute("SELECT * FROM Users WHERE email = %s;", (user.email,))
        db_user = cur.fetchone()
        
        # Kiểm tra tài khoản có tồn tại và mật khẩu có khớp không
        if not db_user or not pwd_context.verify(user.password, db_user['password_hash']):
            raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
            
        # Tạo JWT Token có hạn sử dụng 24 giờ
        expire = datetime.utcnow() + timedelta(hours=24)
        token_data = {
            "user_id": db_user['id'], 
            "role": db_user['role'], 
            "exp": expire
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "message": "Đăng nhập thành công!", 
            "access_token": token, 
            "role": db_user['role'],
            "full_name": db_user['full_name']
        }
    finally:
        cur.close()
        conn.close()