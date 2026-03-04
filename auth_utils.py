from passlib.context import CryptContext

# Khởi tạo công cụ băm mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Băm mật khẩu trước khi lưu vào Database"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu người dùng nhập có khớp với mật khẩu đã băm không"""
    return pwd_context.verify(plain_password, hashed_password)