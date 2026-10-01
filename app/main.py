from fastapi import FastAPI, Depends, Path, Query
from .discover.api import DiscoverRoutes
from typing import List, Optional
from .auth.api import AuthRoutes
from .watchlist.api import WatchListRoutes
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlmodel import Session
from app.database import init_db, get_session
from app.models import User, Watchlist, DiaryEntry
from .diaryentry.api import DiaryEntryRoutes

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
async def root():
    return {"message": "It's working, you fool"}

app.include_router(DiscoverRoutes, prefix="/discover")
app.include_router(AuthRoutes, prefix="/auth")
app.include_router(WatchListRoutes, prefix="/watchlist")
app.include_router(DiaryEntryRoutes, prefix="/diaryentry")