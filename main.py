import uvicorn
from fastapi import FastAPI

from app.routes.video_routes import video_router

from app.routes.auth_routes import auth_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(video_router)



if __name__ == "__main__":
    uvicorn.run(app="main:app", port=8000, reload=True)
