from prisma import Prisma
from features.auth.jwt_handler import JWTHandler


class AuthService:
    def __init__(self, db: Prisma, jwtHandler: JWTHandler):
        self.db = db
        self.jwtHandler = jwtHandler

    async def register(self, username: str, password: str) -> dict:
        existing = await self.db.user.find_unique(where={"username": username})
        if existing:
            raise ValueError("Username already registered")

        user = await self.db.user.create(data={
            "username": username,
            "password": password,
        })

        token = self.jwtHandler.create_token(user.id)
        return token

    async def login(self, username: str, password: str) -> dict:
        user = await self.db.user.find_unique(where={"username": username})
        if not user or password != user.password:
            raise ValueError("Invalid credentials")

        token = self.jwtHandler.create_token(user.id)
        return token
