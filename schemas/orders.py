from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    address: str
    note: Optional[str] = None
    total_amount: float
    products: List[Dict[str, Any]]