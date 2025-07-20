from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi import WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from auth_utils import hash_password, verify_password, create_access_token, verify_token
from schemas import UserCreate, UserLogin, UserResponse, Token, GameResponse, GameCreate, ResultResponse, ResultCreate, CommentCreate, CommentResponse
from models import User, Game
from database import engine, Base, get_db
from crud import create_game as create_game_crud
from crud import get_games as get_games_crud
from crud import game_detail
from crud import delete_game as delete_game_crud
from crud import create_result as create_result_crud
from crud import results_detail
from crud import create_comment_crud, get_comments_by_game, delete_comment_crud
from fastapi.middleware.cors import CORSMiddleware



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

#게임 생성 

@app.post("/games", response_model=GameResponse)
def create_game(
    game_data: GameCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    return create_game_crud(db, game_data, created_by=current_user.id)

#게임 목록 조회
@app.get("/games", response_model=list[GameResponse])
def list_games(db: Session = Depends(get_db)):
    return get_games_crud(db)

#게임 상세 조회
@app.get("/games/{game_id}", response_model=GameResponse)
def read_game(game_id: int, db: Session = Depends(get_db)):
    game = game_detail(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

#게임 삭제
@app.delete("/games/{game_id}")
def delete_game_endpoint(game_id:int, db:Session = Depends(get_db), current_user = Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.created_by != current_user.id :
        raise HTTPException(status_code=403, detail="Not authorized to delete this game")
    
    delete_game_crud(db, game_id)
    return {"message": "Game deleted successfully"}

#게임 결과 저장
@app.post("/games/{game_id}/results", response_model=ResultResponse)
async def create_result_save(game_id: int, result_data: ResultCreate,background_tasks: BackgroundTasks,  db: Session = Depends(get_db) ):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    result = create_result_crud(db, game_id, result_data)
    
    print(f"📡 브로드캐스트 실행: 게임 {game_id}")

    background_tasks.add_task(
        broadcast_result, game_id, {
            "player_name": result.player_name,
            "time_token": result.time_token,
            "found_words": result.found_words,
            "create_at": str(result.create_at)
        })
    
    
    return result

#게임 결과 조회
@app.get("/games/{game_id}/results", response_model=list[ResultResponse])
def results_list(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return results_detail(db, game_id)

#WebSocket
game_connections: dict[int, list[WebSocket]] = {}

@app.websocket("/ws/games/{game_id}/results")
async def websocket_game_results(websocket: WebSocket, game_id: int):
    await websocket.accept()
    print(f" WebSocket 연결됨 → 게임 {game_id}")
    
    if game_id not in game_connections:
        game_connections[game_id] = []
    game_connections[game_id].append(websocket)
    print(f"WebSocket connected for game {game_id}, current connections {len(game_connections[game_id])}명")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        game_connections[game_id].remove(websocket)
        print(f"WebSocket disconnecting -> game {game_id}, current connections {len(game_connections[game_id])}명")
        
#브로드캐스트 함수
async def broadcast_result(game_id: int, result_data: dict):
    if game_id in game_connections:
        for ws in game_connections[game_id]:
            await ws.send_json(result_data)
        print (f"game {game_id} 접속자에게 결과 전송됨")
        
#댓글 작성
@app.post("/games/{game_id}/comments", response_model=CommentResponse)
def create_comment(game_id: int, comment_data: CommentCreate, 
                   db: Session = Depends(get_db), 
                   current_user=Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    comment = create_comment_crud(db, game_id, current_user.id, comment_data.content)
    return comment


#댓글 조회
@app.get("/games/{game_id}/comments", response_model=list[CommentResponse])
def list_comments(game_id: int, db: Session = Depends(get_db)):
    comments = get_comments_by_game(db, game_id)
    return comments


#댓글 삭제
@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: int,
                   db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    result = delete_comment_crud(db, comment_id, current_user.id)
    if result == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if result == "not_authorized":
        raise HTTPException(status_code=403, detail="Not authorized or comment not found")
    return {"message": "Comment deleted successfully"}

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)