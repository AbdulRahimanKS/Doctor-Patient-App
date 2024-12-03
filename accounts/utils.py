import jwt
from DoctorApp.settings import SECRET_KEY
from datetime import datetime, timedelta
from accounts.models import CustomUser


def generate_jwt_token(user):
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    print("User", user)
    print("Id", user.id)
    payload = {
        'user_id': user.id,
        'username': user.name,
        'exp': expiration_time
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def validate_jwt_token(token):
    print("called")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        print("Payload", payload)
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid expired")
        return None
