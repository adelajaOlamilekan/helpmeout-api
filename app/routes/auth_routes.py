import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, APIRouter, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_models import (
    User,
    UserResponse,
    UserAuthentication,
    LogoutResponse,
)
from app.services.services import is_logged_in

auth_router = APIRouter(prefix="/srce/api")

# Load environment variables from .env file
load_dotenv()


@auth_router.post("/signup/", response_model=UserResponse)
async def signup_user(user: UserAuthentication, db: Session = Depends(get_db)):
    try:
        # converting password to array of bytes
        hashed_password = user.password

        pw_bytes = hashed_password.encode("utf-8")

        # generating the salt
        salt = bcrypt.gensalt()

        # Hashing the password
        pw_hash = bcrypt.hashpw(pw_bytes, salt)

        new_user = User(username=user.username, hashed_password=pw_hash)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()

        return UserResponse(
            message="User registered successfully", status_code=201, data=None
        )

    except IntegrityError:
        raise HTTPException(status_code=400, detail="Username is not unique")


@auth_router.post("/login/", response_model=UserResponse)
async def login_user(
    user: UserAuthentication, request: Request, db: Session = Depends(get_db)
):
    # checking if the user is currently logged in
    user_is_loggedin = is_logged_in(request)

    if user_is_loggedin:
        return UserResponse(
            status_code=401, message="User Already Logged in", data=None
        )

    needed_user = db.query(User).filter_by(username=user.username).first()

    if not needed_user:
        return UserResponse(status_code=403, message="Invalid User", data=None)

    # converting password to array of bytes
    provided_password = user.password

    hashed_password = provided_password.encode("utf-8")

    actual_user_password = needed_user.hashed_password

    print(hashed_password, actual_user_password)

    # Validating the entered password
    result = bcrypt.checkpw(hashed_password, actual_user_password)

    if not result:
        return UserResponse(
            status_code=403, message="Invalid Password.", data=None
        )

    # Create Session for User
    request.session["username"] = needed_user.username
    request.session["logged_in"] = True

    db.close()

    return UserResponse(status_code=200, message="Login Successful", data=None)


@auth_router.post("/logout/")
async def logout_user(request: Request, db: Session = Depends(get_db)):
    # checking if the user is currently logged in
    user_is_loggedin = is_logged_in(request)

    if user_is_loggedin:
        del request.session["username"]
        del request.session["logged_in"]

        return LogoutResponse(
            status_code=200, message="User Logged out successfully"
        )
    else:
        # User is not logged in, return an error
        return LogoutResponse(status_code=401, message="User not logged in")
