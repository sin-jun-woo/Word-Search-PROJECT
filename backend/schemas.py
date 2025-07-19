from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

#회원가입
class UserCreate(BaseModel):
    username: str   
    email: EmailStr
    password: str

#로그인
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
#사용자 응답
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    create_at: datetime
    
    class config:
        from_attributes = True
        
#jwt 토큰 응답
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
