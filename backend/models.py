from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

#유저
class User(Base):
    __tablename__ = "Users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)   
    create_at = Column(DateTime, default=datetime.utcnow)
    
    games = relationship("Game", back_populates="creator")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    
#게임    
class Game(Base):
    __tablename__ = "Games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    word_list = Column(Text)
    grid = Column(Text)
    grid_size = Column(Integer)
    created_by = Column(Integer, ForeignKey("Users.id"))
    create_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("User", back_populates="games")
    results = relationship("Result", back_populates="game")
    comments = relationship("Comment", back_populates="game", cascade="all, delete-orphan")
    
#결과
class Result(Base):
    __tablename__ = "Results"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("Games.id"))
    player_name = Column(String, nullable=False)
    time_token = Column(Integer)
    found_words = Column(String)
    create_at = Column(DateTime, default=datetime.utcnow)
    
    game = relationship("Game", back_populates="results")

#댓글    
class Comment(Base):
    __tablename__ = "Comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(Integer, ForeignKey("Games.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="comments")
    game = relationship("Game", back_populates="comments")
