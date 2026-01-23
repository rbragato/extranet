from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)

    users = relationship("User", back_populates="group")
    prices = relationship("PriceItem", back_populates="group", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    first_name = Column(String(100), nullable=False, default="")
    last_name = Column(String(100), nullable=False, default="")
    avatar_filename = Column(String(255), nullable=True)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    group = relationship("Group", back_populates="users")

    created_at = Column(DateTime, nullable=False, server_default=func.now())


class PriceItem(Base):
    __tablename__ = "price_items"

    id = Column(Integer, primary_key=True)
    label = Column(String(200), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    group = relationship("Group", back_populates="prices")

    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
