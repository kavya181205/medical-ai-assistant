from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schema.auth import EmailRequest, OTPVerifyRequest
from app.schema.user import UserInCreate, UserOutput, UserInLogin, UserWithToken

from app.core.database import get_db
from app.service.userService import UserService

# from app.utils.otp import generate_otp, save_otp, verify_otp
# from app.utils.email import send_email_otp

from sendOTP import send_email_otp, generate_otp, save_otp, verify_otp

from google.oauth2 import id_token
from google.auth.transport import requests


authRouter = APIRouter()

# ==============================
# LOGIN
# ==============================

@authRouter.post("/login", response_model=UserWithToken)
def login(loginDetails: UserInLogin, session: Session = Depends(get_db)):
    return UserService(session=session).login(login_details=loginDetails)


# ==============================
# OTP FLOW
# ==============================

verified_emails = set()


def mark_verified(email):
    verified_emails.add(email)


def is_email_verified(email):
    return email in verified_emails


@authRouter.post("/send-otp")
def send_otp_api(data: EmailRequest):
    email = data.email

    otp = generate_otp()
    save_otp(email, otp)

    send_email_otp(email, otp)

    print(f"OTP for {email}: {otp}")  # Debug

    return {"message": "OTP sent successfully"}


@authRouter.post("/verify-otp")
def verify_otp_api(data: OTPVerifyRequest):
    if verify_otp(data.email, data.otp):
        mark_verified(data.email)
        return {"message": "OTP verified"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")


# ==============================
# SIGNUP (WITH OTP CHECK)
# ==============================

@authRouter.post("/signup", status_code=201, response_model=UserOutput)
def signup(signUpDetails: UserInCreate, session: Session = Depends(get_db)):

    if not is_email_verified(signUpDetails.email):
        raise HTTPException(status_code=400, detail="Email not verified")

    return UserService(session=session).signup(user_details=signUpDetails)


# ==============================
# GOOGLE AUTH
# ==============================

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
        raise HTTPException(status_code=400, detail=str(e))


@authRouter.post("/google/signup")
def google_signup(payload: dict, session: Session = Depends(get_db)):

    token = payload.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="Token missing")

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request()
        )

        if idinfo["aud"] != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid audience")

        email = idinfo["email"]
        full_name = idinfo.get("name", "User")

        parts = full_name.split(" ")
        first_name = parts[0]
        last_name = parts[-1] if len(parts) > 1 else ""

        return UserService(session=session).google_signup(
            email=email,
            first_name=first_name,
            last_name=last_name
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))