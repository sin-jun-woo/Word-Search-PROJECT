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
    
#게임 생성 요청
class GameCreate(BaseModel):
    title: str
    description: Optional[str] = None
    word_list: List[str]
    
#게임 응답
class GameResponse(BaseModel):
    id :int
    title: str
    description: Optional[str] = None
    word_list: str
    created_by: int
    create_at: datetime
    
    class config:
        from_attributes = True
        
#게임 결과 저장
class ResultCreate(BaseModel):
    player_name: str
    time_token: int
    found_words : List[str]
    
class ResultResponse(BaseModel):
    id: int
    game_id: int
    player_name: str
    time_token: int
    found_words: str
    create_at: datetime
    
    class config:
        from_attributes = True
    
#댓글     
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass
    
class CommentResponse(CommentBase):
    id: int
    user_id: int
    game_id: int
    created_at: datetime
    
    class config:
        orm_mode = True