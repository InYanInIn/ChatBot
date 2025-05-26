from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from authentication.pswd_service import hash_password
from models.User import User


async def create_user(
        db: AsyncSession,
        username: str,
        password: str
):
    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_username(
        db: AsyncSession,
        username: str
):
    result = await db.execute(select(User).filter_by(username=username))
    user = result.scalars().first()
    return user
