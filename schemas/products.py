from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.products import Products


class ProductsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(self, skip=0, limit=20, query_dict=None, sort=None):
        stmt = select(Products).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return {
            "items": items,
            "total": len(items),
            "skip": skip,
            "limit": limit
        }

    async def get_by_id(self, id: int):
        result = await self.db.execute(
            select(Products).where(Products.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict):
        product = Products(**data)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, id: int, data: dict):
        product = await self.get_by_id(id)
        if not product:
            return None

        for key, value in data.items():
            setattr(product, key, value)

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, id: int):
        product = await self.get_by_id(id)
        if not product:
            return False

        await self.db.delete(product)
        await self.db.commit()
        return True
