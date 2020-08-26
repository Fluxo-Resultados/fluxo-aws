import boto3
from boto3.dynamodb.conditions import Key
from cerberus import Validator
import json
from .json_encoder import json_encoder
from decimal import Decimal


class SchemaError(Exception):
    pass


class DynamodbTable:
    def __init__(self, table_name, schema, hash_key=None, partition_key=None):
        self.table_name = table_name
        self.schema = schema
        self.resource = boto3.resource("dynamodb")
        self.client = boto3.client("dynamodb")
        self.table = self.resource.Table(table_name)
        self.hash_key = hash_key
        self.partition_key = partition_key
        self.validator = Validator(schema)

    def exists(self, id, hash_key=None):
        key = hash_key or self.hash_key
        try:
            if self.table.query(KeyConditionExpression=Key(key).eq(id)).get(
                "Items", []
            ):
                return True
            else:
                return False
        except self.client.exceptions.ResourceNotFoundException:
            return False

    def get_by_hash_key(self, id, hash_key=None):
        key = hash_key or self.hash_key
        try:
            return self.table.query(KeyConditionExpression=Key(key).eq(id)).get(
                "Items", []
            )
        except self.client.exceptions.ResourceNotFoundException:
            return []

    def get_item(self, data):
        return self.table.get_item(Key=data).get("Item", {})

    def query_items(self, key, data):
        return self.table.query(KeyConditionExpression=Key(key)).eq(data).get("Items", [])

    def add(self, data):
        if not self.validator.validate(data):
            raise SchemaError(self.validator.errors)

        data = json.loads(json.dumps(data, default=json_encoder), parse_float=Decimal)

        return self.table.put_item(Item=data)

    def update(self, data, key):
        item = self.get_item(key)

        if item:
            item.update(data)
            return self.table.put_item(Item=item)

    def delete(self, key: dict):
        return self.table.delete_item(Key=key)
