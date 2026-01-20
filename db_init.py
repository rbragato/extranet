import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from models import Base, User

def db_url_from_env() -> str:
    host = os.getenv("MYSQL_HOST", "db")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DATABASE", "extranet")
    user = os.getenv("MYSQL_USER", "extranet_user")
    pwd = os.getenv("MYSQL_PASSWORD", "extranet_pass")
    return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"

def init_db():
    engine = create_engine(db_url_from_env(), pool_pre_ping=True)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    seed_email = os.getenv("SEED_ADMIN_EMAIL", "admin@local").strip().lower()
    seed_password = os.getenv("SEED_ADMIN_PASSWORD", "Admin123!")
    seed_first = os.getenv("SEED_ADMIN_FIRSTNAME", "Admin")
    seed_last = os.getenv("SEED_ADMIN_LASTNAME", "Local")

    exists = session.query(User).filter(User.email == seed_email).first()
    if not exists:
        u = User(
            email=seed_email,
            password_hash=generate_password_hash(seed_password),
            first_name=seed_first,
            last_name=seed_last,
            avatar_filename=None,
        )
        session.add(u)
        session.commit()

    session.close()
    engine.dispose()
