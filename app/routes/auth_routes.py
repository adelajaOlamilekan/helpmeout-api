from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql.expression import select
from sqlalchemy.exc import IntegrityError
from app.models.user_models import UserRequest, User, UserResponse, UserAuthentication, LogoutResponse

import bcrypt
import os 
from dotenv import load_dotenv
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuthError
from starlette.responses import HTMLResponse



from social_core.backends.facebook import FacebookOAuth2
from social_core.backends.google import GoogleOAuth2
from social_core.utils import slugify

auth_router = APIRouter(prefix="/srce/api")
# auth_router = APIRouter()

# Load environment variables from .env file
load_dotenv()

# OAuth settings
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or None
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or None

if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise BaseException('Missing env variables')


# Set up oauth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Set up the middleware to read the request session
# SECRET_KEY = os.environ.get('SECRET_KEY') or None
# if SECRET_KEY is None:
#     raise 'Missing SECRET_KEY'

# auth_router.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@auth_router.get('/')
def public(request: Request):
    user = request.session.get('user')
    if user:
        name = user.get('name')
        return HTMLResponse(f'<p>Hello {name}!</p><a href=/logout>Logout</a>')
    return HTMLResponse('<a href=/srce/api/google_login>Login</a>')

@auth_router.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@auth_router.post("/signup/", response_model=UserResponse)
async def signup_user(user: UserAuthentication, db: Session= Depends(get_db)):
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
async def login_user(user: UserAuthentication, request: Request, db: Session= Depends(get_db)):
    
    #checking if the user is currently logged in
    if "username" in request.session and "logged_in" in request.session:
        return UserResponse(status_code=401, message="User Already Logged in", data=None)

    needed_user = db.query(User).filter_by(username=user.username).first()

    if not needed_user:
         return UserResponse(status_code=403, message="Invalid User", data=None)

    # converting password to array of bytes 
    provided_password = user.password

    hashed_password = provided_password.encode('utf-8') 

    actual_user_password = needed_user.hashed_password
    
    print(hashed_password, actual_user_password)

    # Validatig the entered password
    result = bcrypt.checkpw(hashed_password, actual_user_password)

    if not result:
        return UserResponse(status_code=403, message="Invalid Password.", data=None)
    
    #Create Session for User
    request.session["username"] = needed_user.username
    request.session["logged_in"] = True

    db.close()

    return UserResponse(status_code=200, message="Login Successful", data=None)

@auth_router.post("/logout")
async def logout_user(request: Request, db: Session = Depends(get_db)):

    if "username" in request.session and "logged_in" in request.session:
        del request.session["username"]
        del request.session["logged_in"]

        return LogoutResponse(status_code=200, message="User Logged out successfully")
    else:
        # User is not logged in, return an error
        return LogoutResponse(status_code=401, message="User not logged in")
    
# Function to fetch user info from Facebook using the token
async def get_facebook_user(token: str):
    # Implement the logic to retrieve user data from Facebook API using 'token'
    # Example: Use 'httpx' library to make a GET request to Facebook API
    # Parse the response and return user data
    return {"id": 1, "username": "facebook_user"}

# Function to fetch user info from Google using the token
async def get_google_user(token: str):
    # Implement the logic to retrieve user data from Google API using 'token'
    # Example: Use 'httpx' library to make a GET request to Google API
    # Parse the response and return user data
    return {"id": 2, "username": "google_user"}

# Facebook Login Route
@auth_router.get("/login/facebook")
async def login_with_facebook(token: str = Depends(oauth2_scheme), db: Session= Depends(get_db)):
    user = await get_facebook_user(token)
    if user:
        # Check if the user exists in your database or create a new one
        existing_user = db.query(User).filter_by(username=user["username"]).first()
        if not existing_user:
            # Create a new user if not found
            new_user = User(username=user["username"])
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
        db.close()
        return {"message": "Facebook Login Successful", "user": user}
    else:
        raise HTTPException(status_code=401, detail="Facebook login failed")

# Google Login Route
@auth_router.get('/google_login/')
async def login(request: Request):
    # print("Hello")
    redirect_uri = "http://127.0.0.1:8000/srce/api/google_auth/"  # This creates the url for the /auth endpoint
    # return redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)

@auth_router.get('/google_auth')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
        access_token = access_token.get("id_token")
        print(access_token)
        # return access_token.get("access_token")
        user_data = await oauth.google.parse_id_token(request, access_token)
        print(user_data)
        request.session['user'] = dict(user_data)

        return RedirectResponse(url='http://127.0.0.1:8000/srce/api/')
    except OAuthError as e:
        # Handle the OAuth2 error, e.g., redirect to an error page or log the error
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# @auth_router.get("/login/google")
# async def login_with_google(token: str = Depends(oauth2_scheme), db: Session=Depends(get_db)):
#     user = await get_google_user(token)
#     if user:
#         existing_user = db.query(User).filter_by(username=user["username"]).first()
#         if not existing_user:
#             # Create a new user if not found
#             new_user = User(username=user["username"])
#             db.add(new_user)
#             db.commit()
#             db.refresh(new_user)
#         db.close()
#         return {"message": "Google Login Successful", "user": user}
#     else:
#         raise HTTPException(status_code=401, detail="Google login failed")