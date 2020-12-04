from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError, DecodeError
from base64 import b64decode
from .json_encoder import json_encoder
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


class AuthException(Exception):
    pass


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data, expires_delta, secret_key, has_expiration=True):
    to_encode = data.copy()
    to_encode = json.loads(json.dumps(to_encode, default=json_encoder))

    if has_expiration:
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


def decode_basic_token(authorization):
    """Decode basic auth token using base64 decode method

    :param authorization: valid authorization token string
    :raise: AuthException if there is any exception
    :return: dist object {"username":"<username>", "password":"<password>"}
    """
    authorization = b64decode(authorization).decode()
    authorization = authorization.split(":")
    if len(authorization) < 2:
        raise AuthException("Username or password is missing in basic token.")
    else:
        return {"username": authorization[0], "password": authorization[-1]}


def get_header_field_token(authorization_header):
    """Get Auth mechanism and token from Authorization header field value

    :param authorization_header: Authorization header field string value
    :raise: AuthException if there is any exception
    :return: dist object {"token":"<token>", "type":"auth mechanism type: basic|bearer"}
    """
    authorization_token = authorization_header.split(" ")
    token = authorization_token[-1]
    if len(authorization_token) < 2:
        raise AuthException("Invalid token.")
    else:
        if authorization_token[0].lower() not in ["basic", "bearer"]:
            raise AuthException("Unspported auth mechanism.")
        elif authorization_token[0].lower() == "basic":
            return {"token": str(token), "type": authorization_token[0].lower()}
        elif authorization_token[0].lower() == "bearer":
            return {"token": str(token), "type": authorization_token[0].lower()}
