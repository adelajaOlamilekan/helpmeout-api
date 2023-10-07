import uvicorn
from app import create_app as helpmeout


# Create the app
app = helpmeout()

if __name__ == "__main__":
    # Run the app using uvicorn on port 8080
    uvicorn.run(app="main:app", port=8000, reload=True)
