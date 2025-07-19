import json
from sqlalchemy.orm import Session
from models import Game
from schemas import GameCreate

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