import jwt
from DoctorApp.settings import SECRET_KEY
from datetime import datetime, timedelta


def generate_jwt_token(user):
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    
    payload = {
        'user_id': user.id,
        'username': user.name,
        'exp': expiration_time
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def validate_jwt_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
