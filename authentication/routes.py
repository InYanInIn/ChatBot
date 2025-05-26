from fastapi import APIRouter, Depends, HTTPException
from authentication.schemas import UserCreate, Token
from authentication.user_handling import create_user, get_user_by_username
from authentication.pswd_service import verify_password
from authentication.jwt_handler import create_access_token
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register_user(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_username(db, user_data.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = await create_user(db, user_data.username, user_data.password)

    return {"id": new_user.id, "username": new_user.username}

@router.post("/login", response_model=Token)
async def login_user(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_username(db, user_data.username)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.id})

    return {"access_token": token}
