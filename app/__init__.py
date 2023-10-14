""" Initializes the FastAPI app. """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routes.video_routes import router
from app.routes.auth_routes import auth_router


def create_app() -> FastAPI:
    """
    Creates the FastAPI app.

    Returns:
        FastAPI: The FastAPI app.
    """
    # Create the FastAPI app
    app = FastAPI()

    # Initialize CORS
    origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://helpmeout-dev.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    # Include routes
    app.include_router(router)
    app.include_router(auth_router)

    app.add_middleware(SessionMiddleware, secret_key="")

    return app
