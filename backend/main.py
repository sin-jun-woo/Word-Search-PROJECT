from fastapi import FastAPI
from database import engine, Base



app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"Word Search 백엔드 실행중"}


