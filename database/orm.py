from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.models import Base, User, Favorite
from sqlalchemy import select
from config import config

engine = create_async_engine(config.DB_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_user(tg_id: int, username: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id, username=username))
            await session.commit()

async def add_favorite(tg_id: int, name: str, url: str, salary: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            # Проверка на дубликаты пропущена для краткости, можно добавить
            session.add(Favorite(user_id=user.id, vacancy_name=name, vacancy_url=url, salary=salary))
            await session.commit()

async def get_favorites(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return []
        result = await session.execute(select(Favorite).where(Favorite.user_id == user.id))
        return result.scalars().all()