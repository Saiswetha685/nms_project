from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.security import verify_password, create_access_token
from backend.app.auth.deps import get_current_user
from backend.app.schemas.user import UserLogin, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["email"], "role": user.get("role", "operator")})
    user_resp = UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user.get("role", "operator"),
        created_at=user["created_at"]
    )
    return TokenResponse(access_token=access_token, token_type="bearer", user=user_resp)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        name=current_user["name"],
        email=current_user["email"],
        role=current_user.get("role", "operator"),
        created_at=current_user["created_at"]
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Successfully logged out"}
