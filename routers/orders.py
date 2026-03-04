from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from dependencies.auth import get_current_user
from models.orders import Order
from schemas.orders import OrderCreate
from schemas.auth import UserResponse

# API này sẽ tự động gắn prefix là /api/v1/orders
router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

@router.post("")
async def create_order(
    order: OrderCreate, 
    current_user: UserResponse = Depends(get_current_user), # 🔒 Yêu cầu đăng nhập mới được mua
    db: AsyncSession = Depends(get_db)
):
    """API Lưu đơn hàng từ Giỏ hàng (Checkout)"""
    new_order = Order(
        user_id=current_user.id,
        customer_name=order.customer_name,
        phone=order.phone,
        address=order.address,
        total_amount=order.total_amount,
        products=order.products,
        status="pending"
    )
    
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    return {"message": "Đặt hàng thành công!", "order_id": new_order.id}