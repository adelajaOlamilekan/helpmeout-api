from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.video_routes import router
from app.routes.auth_routes import auth_router
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

load_dotenv()



def create_app():
    # Create the FastAPI app
    app = FastAPI()

    # Initialize CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router)
    app.include_router(auth_router)

    SECRET_KEY = os.environ.get('SECRET_KEY') or None

    if SECRET_KEY is None:
        raise 'Missing SECRET_KEY'
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

    return app
