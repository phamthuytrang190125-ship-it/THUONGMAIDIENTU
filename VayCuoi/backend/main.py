from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, dress, order

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["Xác thực"])
app.include_router(dress.router, tags=["Sản phẩm Váy"])
app.include_router(order.router, tags=["Đơn hàng"])

@app.get("/")
def home():
    return {"message": "Chào mừng đến với API Hệ thống cho thuê Váy Cưới!"}