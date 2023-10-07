from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import select
from app.models.user_models import UserSchema
from sqlalchemy.orm import Session



auth_router = APIRouter(prefix="/srce/api")

@auth_router.post("/signup/")
async def signup_user(user: UserSchema, db: Session= Depends(get_db)):
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()