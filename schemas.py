from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# 1. Schema cho Form Đăng ký / Đăng nhập
class UserCreate(BaseModel):
    email: str
    password: str

# 2. Schema trả về thông tin User
class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True

# 3. Schema cho Form Đặt hàng (Checkout)
class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    address: str
    note: Optional[str] = None
    total_amount: float
    products: List[Dict[str, Any]] # Nhận mảng các sản phẩm trong giỏ hàng