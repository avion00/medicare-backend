import jwt
import datetime
from config import Config

def generate_access_token(user_id):
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=Config.JWT_EXPIRATION_SECONDS),
        "iat": datetime.datetime.utcnow(),
        "sub": str(user_id)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')


def decode_access_token(token):
    try:
        payload = jwt.decode(token,Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None