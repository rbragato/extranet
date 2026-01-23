import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from models import Base, User, Group

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

    # 1) Ensure groups
    def get_or_create_group(name: str) -> Group:
        g = session.execute(select(Group).where(Group.name == name)).scalar_one_or_none()
        if not g:
            g = Group(name=name)
            session.add(g)
            session.commit()
        return g

    gA = get_or_create_group("GroupeA")
    gB = get_or_create_group("GroupeB")

    # 2) Ensure users
    def ensure_user(email: str, password: str, first: str, last: str, group: Group):
        email = email.strip().lower()
        u = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not u:
            u = User(
                email=email,
                password_hash=generate_password_hash(password),
                first_name=first,
                last_name=last,
                avatar_filename=None,
                group_id=group.id
            )
            session.add(u)
            session.commit()

    ensure_user("user1@demo.fr", "user1@demo.fr", "User", "One", gA)
    ensure_user("user2@demo.fr", "user2@demo.fr", "User", "Two", gB)
    ensure_user("user3@demo.fr", "user3@demo.fr", "User", "Three", gA)

    session.close()
    engine.dispose()
