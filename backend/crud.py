import json
import random
from sqlalchemy.orm import Session, joinedload
from models import Game, Result, Comment, User
from schemas import GameCreate, ResultCreate

def generate_word_search_grid(words: list[str], grid_size: int = 10):
    grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
    words = [w.upper() for w in words]

    directions = [
        (0, 1), (1, 0), (1, 1), (1, -1),
        (0, -1), (-1, 0), (-1, -1), (-1, 1)
    ]

    for word in sorted(words, key=len, reverse=True):
        placed = False
        for _ in range(200): # 단어 배치를 200번 시도
            direction = random.choice(directions)
            dr, dc = direction
            
            start_row = random.randint(0, grid_size - 1)
            start_col = random.randint(0, grid_size - 1)
            
            end_row = start_row + (len(word) - 1) * dr
            end_col = start_col + (len(word) - 1) * dc

            if not (0 <= end_row < grid_size and 0 <= end_col < grid_size):
                continue

            can_place = True
            for i in range(len(word)):
                row, col = start_row + i * dr, start_col + i * dc
                if grid[row][col] != '' and grid[row][col] != word[i]:
                    can_place = False
                    break
            
            if can_place:
                for i in range(len(word)):
                    row, col = start_row + i * dr, start_col + i * dc
                    grid[row][col] = word[i]
                placed = True
                break
        
        if not placed:
            print(f"Warning: Could not place the word '{word}'")

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    flat_grid = [grid[r][c] or random.choice(alphabet) for r in range(grid_size) for c in range(grid_size)]
            
    return json.dumps(flat_grid)

# 게임 생성
def create_game(db: Session, game_data: GameCreate, created_by: int):
    grid_size = 10
    grid_json = generate_word_search_grid(game_data.word_list, grid_size)
    game = Game(
        title=game_data.title,
        description=game_data.description,
        word_list=json.dumps([w.upper() for w in game_data.word_list]),
        grid=grid_json,
        grid_size=grid_size,
        created_by=created_by
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


# 게임 목록 조회
def get_games(db:Session):
    return db.query(Game).options(joinedload(Game.creator)).order_by(Game.create_at.desc()).all()

# 게임 상세 조회
def game_detail(db:Session, game_id:int):
    return db.query(Game).options(joinedload(Game.creator)).filter(Game.id == game_id).first()

#게임 삭제
def delete_game(db:Session, game_id:int):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        db.delete(game)
        db.commit()
        return True
    return False

#게임 결과 저장
def create_result(db:Session, game_id:int, result_data:ResultCreate):
    found_words_json = json.dumps(result_data.found_words, ensure_ascii=False)
    result = Result(
        game_id = game_id,
        player_name = result_data.player_name,
        time_token = result_data.time_token,
        found_words = found_words_json
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    
    return result

#게임 결과 조회
def results_detail(db:Session, game_id:int):
    return db.query(Result).filter(Result.game_id == game_id).all()

#댓글 기능
def create_comment_crud(db: Session, game_id: int, user_id: int, content: str):
    comment = Comment(
        content=content,
        user_id=user_id,
        game_id=game_id
        )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def get_comments_by_game(db: Session, game_id: int):
    return db.query(Comment).options(joinedload(Comment.user)).filter(Comment.game_id == game_id).order_by(Comment.created_at.desc()).all()

def delete_comment_crud(db: Session, comment_id: int, user_id: int):
    comment = db.query(Comment).options(joinedload(Comment.game)).filter(Comment.id == comment_id).first()

    if not comment:
        return "not_found"

    # 댓글 작성자이거나 게임 제작자인 경우에만 삭제 허용
    is_author = comment.user_id == user_id
    is_game_creator = comment.game.created_by == user_id

    if not (is_author or is_game_creator):
        return "not_authorized"

    # 삭제 실행
    db.delete(comment)
    db.commit()
    return "success"
