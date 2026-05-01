from bcrypt import hashpw,checkpw,gensalt

class HashHelper(object):

    @staticmethod
    def verify_password(plain_password: str,hashed_password: str):
        if checkpw(plain_password.encode('utf-8'),hashed_password.encode('utf-8')):
            return True
        else:
            return False
    
    @staticmethod
    def get_password_hash(password: str):
        return hashpw(password.encode('utf-8'),gensalt()).decode('utf-8')