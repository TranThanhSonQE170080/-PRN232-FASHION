from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

async def get_database(db: AsyncSession = Depends(get_db)):
    """Database session dependency"""
    return db