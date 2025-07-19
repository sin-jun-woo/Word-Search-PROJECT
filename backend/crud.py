import json
from sqlalchemy.orm import Session
from models import Game, Result, Comment
from schemas import GameCreate, ResultCreate

# 게임 생성
def create_game(db: Session, game_data: GameCreate, user_id:int):
    word_list_json = json.dumps(game_data.word_list, ensure_ascii=False)
    
    game = Game(
        title = game_data.title,
        description = game_data.description,
        word_list = word_list_json,
        created_by = user_id
    )
        
    db.add(game)
    db.commit()
    db.refresh(game)
    return game

# 게임 목록 조회
def get_games(db:Session):
    return db.query(Game).all()

# 게임 상세 조회
def game_detail(db:Session, game_id:int):
    return db.query(Game).filter(Game.id == game_id).first()

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
    return db.query(Comment).filter(Comment.game_id == game_id).order_by(Comment.created_at.desc()).all()

def delete_comment_crud(db: Session, comment_id: int, user_id: int):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.user_id == user_id).first()
    print(f"삭제 요청 comment_id: {comment_id}, 요청 user_id: {user_id}")
    if comment:
        print(f"DB에서 찾은 comment -> id: {comment.id}, 작성자 user_id: {comment.user_id}")
    else:
        print("해당 comment_id로 댓글을 찾을 수 없음")
        
    if not comment or comment.user_id != user_id:
        print("삭제 불가: 댓글이 없거나 권한 없음")
        return False  

    # 삭제 실행
    db.delete(comment)
    db.commit()
    print("댓글 삭제 완료!")
    return True
