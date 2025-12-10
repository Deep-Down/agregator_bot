from sqlalchemy import BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)

    favorites = relationship("Favorite", back_populates="user")

class Favorite(Base):
    __tablename__ = 'favorites'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    vacancy_name: Mapped[str] = mapped_column(String)
    vacancy_url: Mapped[str] = mapped_column(String)
    salary: Mapped[str] = mapped_column(String, nullable=True)

    user = relationship("User", back_populates="favorites")