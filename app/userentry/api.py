from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query

UserEntry = APIRouter()

@UserEntry.get("")
async def root():
    return {"message": "Just starting"}