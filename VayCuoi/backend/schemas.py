from pydantic import BaseModel
from datetime import date
from typing import Literal


class UserRegister(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class OrderCreate(BaseModel):
    dress_id: int
    start_date: date
    end_date: date
    shipping_address: str
    payment_method: str


class OrderStatusUpdate(BaseModel):
    status: Literal[
        "PENDING",
        "COMPLETED",
        "CONFIRMED",
        "RENTING",
        "RETURNED",
        "CANCELLED"
    ]

# ==========================================
# THÊM MỚI: Cấu trúc dữ liệu cho form Quyết toán
# ==========================================
class OrderCheckout(BaseModel):
    return_condition: str
    damage_fee: float
    late_fee: float
    note: str = ""