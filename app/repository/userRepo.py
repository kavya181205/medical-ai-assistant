from .base import BaseRepository
from app.models.user import User
from app.schema.user import UserInCreate

class USerRepository(BaseRepository):
    def create_user(self,user: UserInCreate):
        newUser=User(**user.model_dump(exclude_none=True))
        self.session.add(instance=newUser)
        self.session.commit()
        self.session.refresh(instance=newUser)
        return newUser
    
    def user_exist_by_email(self,email: str):
        return bool(self.session.query(User).filter(User.email==email).first())
    
    def get_user_by_email(self,email: str):
        return self.session.query(User).filter(User.email==email).first()
    
    def get_user_by_id(self,user_id: int):
        return self.session.query(User).filter(User.id==user_id).first()