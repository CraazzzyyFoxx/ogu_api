from fastapi import (
    Depends, HTTPException, status
)
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request
from cashews import cache

from config import api

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')


class AuthService:
    @classmethod
    async def requires_authorization(cls, token: str = Depends(oauth2_scheme)):
        if token != api.token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token

