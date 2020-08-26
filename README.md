# Fluxo AWS

Provides a bunch of functions and utils to help you build applications on top of Amazon Web Services Resources. We use this in our web development flow and would love hear suggestions and improvements on this.

## Usage

Just import the function or class that you want to use, and you're good to go

## Functions

### AWS Lambda handlers

1. `prepare_response`

Function Decorator that:
- Allows you to make a response in a tuple format containing `(status_code, body, headers)`. Example: `return 200, {"success": True}`
- If body is `dict` or `list`, runs `json.dumps` function with encoders for `datetime.datetime`, `decimal.Decimal` and `bytes`
- Add CORS headers
- Add JSON content type header
- Defaults your response: 200 for status code, `{}` for body

Usage:
```
from fluxo_aws import prepare_response

@prepare_response
def handler(event, context):
    return 200, {"success": True}
```

2. `event_parser`

Function decorator that transform your event variable to a `ParsedEvent` class, exposing three methods: `body`, `headers` and `query`. It will transform `strings` into `dict`, and parse variables for you.

Usage
```
from fluxo_aws import prepare_response, event_parser

@prepare_response
@event_parser
def handler(event, context):
    print(event.body)
    print(event.headers)
    print(event.query)

    param = event.query.get("param")

    return 200
```

### DynamoDB handlers

1. `DynamodbTable(table_name, schema, hash_key=None, partition_key=None)`

Helper for DynamoDB. schema is a valid cerberus schema dict. This class exposes:

- `exists(id, hash_key=None)`: check if hash key exists in table, returning `True` of `False`
- `get_by_hash_key(id, hash_key=None)`: get a list of records for given hash key
- `add(data)`: insert dict into DynamoDB. Raise `SchemaError` if dict does not match schema with table schema

Usage
```
from fluxo_aws import DynamodbTable, SchemaError

schema = {"name": {"type": "string"}}

table = DynamodbTable("table", schema, hash_key=name)

try:
    table.add({"name": 123})
except SchemaError as e:
    print(f"schema error: {str(e)}")

print(table.exists("test"))
print(table.get_by_hash_key("test"))
```

### Auth handlers

1. `hash_password(password)`

Hashes and salt a password string using `bcrypt` and `HS256`

Usage
```
from fluxo_aws import hash_password

print(hash_password("secret"))
```

2. `verify_password(plain_password, hashed_password)`

Compares a hash string with a password string, returning `True` if matches and `False` if not matches

Usage
```
from fluxo_aws import verify_password

print(verify_password("secret", "..."))
```

3. `create_access_token(data, expires_delta, secret_key)`

Creates a JSON Web Token for data with an expiration delta of `expires_delta`

Usage
```
from fluxo_aws import create_access_token
from uuid import uuid4
from datetime import timedelta

print(create_access_token({"test": True}, timedelta(hours=3), str(uuid4())))
```

4. `decode_token(data, secret_key)`

WIP

### S3 handlers

1. `S3Bucket(bucket_name)`

Helper for S3 Operations. This class exposes:

- `upload_file(file_name, object_name=None)`: upload local file to S3 returns `True` if uploaded successfully else `False`
- `download_file(object_name, file_name=None)`: download S3 file locally
- `create_presigned_url(object_name, action="get_object", expiration=3600)`: creates a presigned URL for S3 object. Returns presigned URL if successfully else returns None

Usage
```
from fluxo_aws import S3Bucket

s3_bucket = S3Bucket("my-test-bucket")
object_name = "test_file.txt"
file_name = "/tmp/text_file.txt"


print(s3_bucket.upload_file(file_name, object_name))

print(s3_bucket.create_presigned_url(object_name, action, expiration))

print(s3_bucket.download_file(object_name, file_name))

```
