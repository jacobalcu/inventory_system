from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)

    async def get_by_sku(self, sku: str) -> Product | None:
        query = select(self.model).where(self.model.sku == sku)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
