from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from auth_utils import hash_password, verify_password, create_access_token, verify_token
from schemas import UserCreate, UserLogin, UserResponse, Token
from models import User
from database import engine, Base, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = HTTPBearer()

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

#사용자 가져오기
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

#회원가입
@app.post("/auth/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

#로그인
@app.post("/auth/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type" : "bearer"}

#내 정보 확인
@app.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user