from fastapi import APIRouter, HTTPException, status

from features.auth.service import AuthService
from features.auth.schema import UserCreate, UserLogin
from features.core.database import db
from features.auth.jwt_handler import JWTHandler

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService(db, JWTHandler())


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate):
    try:
        token = await auth_service.register(body.username, body.password)
        return {'JWT': token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(body: UserLogin):
    try:
        token = await auth_service.login(body.username, body.password)
        return {'JWT': token}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
