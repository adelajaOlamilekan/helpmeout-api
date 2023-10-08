from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import select
from sqlalchemy.exc import IntegrityError
from app.models.user_models import UserRequest, User, UserResponse
from sqlalchemy.orm import Session
import bcrypt



auth_router = APIRouter(prefix="/srce/api")

@auth_router.post("/signup/", response_model=UserResponse)
async def signup_user(user: UserRequest, db: Session= Depends(get_db)):
    try:        
        # converting password to array of bytes 
        hashed_password = user.password

        bytes = hashed_password.encode('utf-8') 

        # generating the salt 
        salt = bcrypt.gensalt() 

        # Hashing the password 
        hash = bcrypt.hashpw(bytes, salt) 

        new_user = User(
            username = user.username,
            hashed_password = hash
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()

        return UserResponse(message = 'User registered successfully',
                        status_code= 201,
                        data= None
                    )
    
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Username is not unique")
        
@auth_router.post("/login/", response_model=UserResponse)
async def login_user(user: UserRequest, db: Session= Depends(get_db)):
    
    needed_user = db.query(User).filter_by(username=user.username).first()

    if not needed_user:
         raise HTTPException(
            detail="Invalid username.", status_code=status.HTTP_403_FORBIDDEN
        )
    
    # print(needed_user, needed_user.username)

    # converting password to array of bytes 
    provided_password = user.password

    hashed_password = provided_password.encode('utf-8') 

    actual_user_password = needed_user.hashed_password
    
    print(hashed_password, actual_user_password)

    # Comapring the entered password and the saved password
    result = bcrypt.checkpw(hashed_password, actual_user_password)

    if not result:
        raise HTTPException(
            detail="Invalid Password.", status_code=status.HTTP_403_FORBIDDEN
        )
    else:
        return UserResponse(status_code=200, message="Login Successful", data=None)