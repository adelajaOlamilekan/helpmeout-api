from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.video_routes import router
from app.routes.auth_routes import auth_router
from starlette.middleware.sessions import SessionMiddleware



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

    app.add_middleware(SessionMiddleware, secret_key="")

    return app
