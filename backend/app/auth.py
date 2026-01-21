from datetime import datetime, timedelta
from typing import Optional

from app.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# JWT Configuration
SECRET_KEY = getattr(settings, 'secret_key', "your-secret-key-change-this-in-production-use-openssl-rand-hex-32")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# OAuth2 scheme for Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class User(BaseModel):
    user_id: str
    username: str
    disabled: Optional[bool] = None


# Mock user database - In production will be replaced with actual database
fake_users_db = {
    "testuser": {
        "user_id": "user_123",
        "username": "testuser",
        "hashed_password": "$5$rounds=535000$/C7zpQGrE7MXebAu$jrAP1CWx/4pIN3CO6sRREGNxNiG4Q6b5JCHrdwydwG8",  # "secret"
        "disabled": False,
    },
    "demo": {
        "user_id": "user_456",
        "username": "demo",
        "hashed_password": "$5$rounds=535000$pdYPIp4U517O2cTu$Gx7eF2XiCCvjUylH3uppFLXfIMebIS19aCtFTms1p89",  # "demo123"
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username
        password: Plain text password
    
    Returns:
        User dict if authenticated, None otherwise
    """
    user = fake_users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token (must include 'sub' claim)
        expires_delta: Optional expiration time delta
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Validate JWT token and return current user.
    
    This dependency extracts and validates the Bearer token,
    preventing IDOR attacks by ensuring user_id comes from the token.
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        Authenticated User object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Find user by user_id in the token
    user = None
    for username, user_data in fake_users_db.items():
        if user_data["user_id"] == token_data.user_id:
            user = User(
                user_id=user_data["user_id"],
                username=user_data["username"],
                disabled=user_data.get("disabled", False)
            )
            break
    
    if user is None:
        raise credentials_exception
    
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user (convenience wrapper).
    
    Args:
        current_user: User from get_current_user dependency
    
    Returns:
        Active User object
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
