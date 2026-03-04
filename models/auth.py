from models.base import Base
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    # ✅ TRẢ LẠI ID LÀ STRING NHƯ CŨ ĐỂ KHÔNG LÀM LỖI DATABASE
    id = Column(String(255), primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    role = Column(String(50), default="user", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # ✅ CHO PHÉP NULL ĐỂ HÀM KHỞI TẠO CŨ KHÔNG BỊ SẬP
    hashed_password = Column(String(255), nullable=True)

class OIDCState(Base):
    __tablename__ = "oidc_states"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), unique=True, index=True, nullable=False)
    nonce = Column(String(255), nullable=False)
    code_verifier = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())