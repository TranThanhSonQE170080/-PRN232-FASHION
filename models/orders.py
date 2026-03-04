from models.base import Base
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # ✅ SỬA THÀNH STRING(255) CHO KHỚP VỚI BẢNG USERS
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False) 
    
    customer_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    address = Column(String(500), nullable=False)
    total_amount = Column(Float, nullable=False)
    products = Column(JSON, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())