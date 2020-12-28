from functools import wraps
from .json_encoder import json_encoder
import json

mapping = {
    bytes: lambda x: x.decode(),
}


def prepare_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not result:
            result = {}
        if type(result) == tuple:
            keys = ["statusCode", "body", "headers"]
            result = {
                keys[i]: mapping.get(type(result[i]), type(result[i]))(result[i])
                for i in range(len(result))
            }
        elif type(result) == int:
            # Assuming status_code
            result = {"statusCode": result}

        status_code = result.get("statusCode", 200)
        body = result.get("body", {})
        headers = result.get("headers", {})
        if type(body) in (dict, list):
            body = json.dumps(body, default=json_encoder)

        if type(headers) != dict:
            raise ValueError("headers must be dict")

        if "Content-Type" not in headers.keys():
            headers["Content-Type"] = "application/json"

        if "Access-Control-Allow-Methods" not in headers.keys():
            headers["Access-Control-Allow-Methods"] = "*"

        if "Access-Control-Allow-Origin" not in headers.keys():
            headers["Access-Control-Allow-Origin"] = "*"

        if "Access-Control-Allow-Credentials" not in headers.keys():
            headers["Access-Control-Allow-Credentials"] = True

        return {"statusCode": status_code, "body": body, "headers": headers}

    return wrapper
