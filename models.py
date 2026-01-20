from sqlalchemy import (
    Column, Integer, String, DateTime, Numeric, ForeignKey, func
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    first_name = Column(String(100), nullable=False, default="")
    last_name = Column(String(100), nullable=False, default="")
    avatar_filename = Column(String(255), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    prices = relationship("PriceItem", back_populates="owner", cascade="all, delete-orphan")


class PriceItem(Base):
    __tablename__ = "price_items"

    id = Column(Integer, primary_key=True)
    label = Column(String(200), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="prices")

    created_at = Column(DateTime, nullable=False, server_default=func.now())
