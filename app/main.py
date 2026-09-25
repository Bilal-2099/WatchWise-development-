from fastapi import FastAPI, Depends, Path, Query
from .discover.api import DiscoverRoutes
from typing import List, Optional
from .auth.api import AuthRoutes
from .userentry.api import UserEntry

from contextlib import asynccontextmanager
from sqlmodel import Session
from app.database import init_db, get_session
from app.models import User, Watchlist, DiaryEntry

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
async def root():
    return {"message": "It's working, you fool"}

@app.post("/diary/log/")
def log_media(entry: DiaryEntry, db: Session = Depends(get_session)):
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "success", "data": entry}

app.include_router(DiscoverRoutes, prefix="/discover")
app.include_router(AuthRoutes, prefix="/auth")
app.include_router(UserEntry, prefix="/userentry")