from core.database import Base
from sqlalchemy import Column, DateTime, Float, Integer, String


class Products(Base):
    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    image = Column(String, nullable=True)
    category = Column(String, nullable=True)
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)
    stock = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)