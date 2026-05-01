from fastapi import APIRouter,Depends
from app.schema.user import UserInCreate,UserOutput,UserInLogin,UserWithToken
from app.core.database import get_db
from app.service.userService import UserService 
from sqlalchemy.orm import Session

authRouter=APIRouter()

@authRouter.post("/login",status_code=200,response_model=UserWithToken)
def login(loginDetails: UserInLogin, session: Session=Depends(get_db)):
    try:
        return UserService(session=session).login(login_details=loginDetails)
    except Exception as e:
        print(e)
        raise e

@authRouter.post("/signup",status_code=201,response_model=UserOutput)
def signUp(signUpDetails: UserInCreate, session: Session=Depends(get_db)):
    try:
        return UserService(session=session).signup(user_details=signUpDetails)
    except Exception as e:
        print(e)
        raise e
    


from fastapi import HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests

GOOGLE_CLIENT_ID = "766510130964-vpvfpfgs2cbn13qhtft6r3orvpnrrds2.apps.googleusercontent.com"

@authRouter.post("/google")
def google_auth(payload: dict, session: Session = Depends(get_db)):

    token = payload.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="Token missing")

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request()
        )

        print("Decoded:", idinfo)

        if idinfo["aud"] != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid audience")

        email = idinfo["email"]

        full_name = idinfo.get("name", "User")
        parts = full_name.split(" ")

        first_name = parts[0]
        last_name = parts[-1] if len(parts) > 1 else ""

        return UserService(session=session).google_login(
            email=email,
            first_name=first_name,
            last_name=last_name
        )

    except Exception as e:
        print("Google Error:", e)
        raise HTTPException(status_code=400, detail=str(e))