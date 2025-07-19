import json
from sqlalchemy.orm import Session
from models import Game, Result
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