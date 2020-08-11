from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError, DecodeError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


class AuthException(Exception):
    pass


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data, expires_delta, secret_key,
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=360)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(data, secret_key):
    try:
        return jwt.decode(data, secret_key, algorithms=ALGORITHM)
    except InvalidSignatureError:
        raise AuthException("Invalid signature.")
    except ExpiredSignatureError:
        raise AuthException("Session expired.")
    except DecodeError:
        raise AuthException("Invalid token.")
