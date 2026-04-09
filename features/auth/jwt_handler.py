from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

load_dotenv()


class JWTHandler:
    def __init__(
        self,
        secret_key: str = os.getenv("SECRET_KEY"),
        algorithm: str = os.getenv("ALGORITHM", "HS256"),
        expiration_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10_080)),
    ):
        if not secret_key:
            raise ValueError("SECRET_KEY is not set in environment variables")

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

    def create_token(self, user_id: int) -> str:
        """Generate a signed JWT for the given user ID."""
        payload = {
            "sub": str(user_id),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.expiration_minutes),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT. Raises ValueError on failure."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError as e:
            raise ValueError(f"Invalid or expired token: {e}")

    def get_user_id(self, token: str) -> int:
        """Extract the user ID from a valid JWT."""
        payload = self.decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Token is missing 'sub' claim")
        return int(user_id)

    def is_valid(self, token: str) -> bool:
        """Return True if the token is valid, False otherwise."""
        try:
            self.decode_token(token)
            return True
        except ValueError:
            return False
