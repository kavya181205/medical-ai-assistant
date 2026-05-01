from app.repository.userRepo import USerRepository
from app.schema.user import UserOutput,UserInCreate,UserInLogin,UserWithToken
from fastapi import HTTPException
from app.core.security.hashhelper import HashHelper
from app.core.security.authhandler import AuthHandler
from sqlalchemy.orm import Session

class UserService:
    def __init__(self, session : Session):
        self.__userRepository = USerRepository(session=session)
    
    def signup(self, user_details : UserInCreate) -> UserOutput:
        if self.__userRepository.user_exist_by_email(email=user_details.email):
            raise HTTPException(status_code=400, detail="Please Login")
        
        hashed_password = HashHelper.get_password_hash(user_details.password)
        user_details.password = hashed_password
        return self.__userRepository.create_user(user_details)
    
    def login(self, login_details : UserInLogin) -> UserWithToken:
        if not self.__userRepository.user_exist_by_email(email=login_details.email):
            raise HTTPException(status_code=400, detail="Please create an Account")
        
        user = self.__userRepository.get_user_by_email(email=login_details.email)
        if HashHelper.verify_password(plain_password=login_details.password, hashed_password=user.password):
            token = AuthHandler.sign_jwt(user_id=user.id)
            if token:
                return UserWithToken(token=token)
            raise HTTPException(status_code=500, detail="Unable to process request")
        raise HTTPException(status_code=400, detail="Please check your Credentials")
    
    def get_user_by_id(self, user_id : int):
        user = self.__userRepository.get_user_by_id(user_id=user_id)
        if user:
            return user
        raise HTTPException(status_code=400, detail="User is not available")

    def google_login(self, email: str, first_name: str, last_name: str):
        user = self.__userRepository.get_user_by_email(email=email)

        if not user:
            user = self.__userRepository.create_user(UserInCreate(
                email=email,
                password="",  # Google users don't need password
                first_name=first_name,
                last_name=last_name
            ))

        token = AuthHandler.sign_jwt(user_id=user.id)

        return UserWithToken(token=token)