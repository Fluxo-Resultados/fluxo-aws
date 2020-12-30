import boto3
from boto3.dynamodb.conditions import Key, Attr
from cerberus import Validator, TypeDefinition
import json
from .json_encoder import json_encoder
from decimal import Decimal
import warnings


class SchemaError(Exception):
    pass


class DynamodbTable:
    def __init__(self, table_name, schema=None, hash_key=None, partition_key=None):
        self.table_name = table_name
        self.schema = schema
        self.resource = boto3.resource("dynamodb")
        self.client = boto3.client("dynamodb")
        self.table = self.resource.Table(table_name)
        self.hash_key = hash_key
        self.partition_key = partition_key

        if self.schema:
            self.validator = Validator(schema)
            self.validator.types_mapping["integer"] = TypeDefinition(
                "integer", (int, Decimal), (bool,)
            )
            self.validator.types_mapping["float"] = TypeDefinition(
                "float", (float, Decimal), ()
            )
            self.validator.types_mapping["number"] = TypeDefinition(
                "number", (int, float, Decimal), (bool,)
            )
        else:
            self.validator = None

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

    def get_by_hash_key(self, id, hash_key=None, index_name=None):
        key = hash_key or self.hash_key
        query_kwargs = {"KeyConditionExpression": Key(key).eq(id)}
        if index_name:
            query_kwargs["IndexName"] = index_name

        try:
            return self.table.query(**query_kwargs).get("Items", [])
        except self.client.exceptions.ResourceNotFoundException:
            return []

    def get_item(self, data):
        return self.table.get_item(Key=data).get("Item", {})

    def query_items(self, data, key, startKey=None, index_name=None):
        if startKey:
            warnings.warn(
                "Start key is deprecated, this method always query all items regardless of the key",
                DeprecationWarning,
            )
        """Query Items from DynamoDB Table

        :param data: query data
        :param key: query field
        :param startKey: default=None
        :return: dist object {"Items": [...items...], "ExclusiveStartKey":"...next page start key(if there is next page)..."}
        """
        if isinstance(key, dict):
            if key["operator"] == "in":
                FilterExpression = Attr(key["range"]).is_in(data["range"])
                KeyConditionExpression = Key(key["hash"]).eq(data["hash"])
                query_kwargs = {
                    "KeyConditionExpression": KeyConditionExpression,
                    "FilterExpression": FilterExpression,
                }
            elif key["operator"] == "between":
                query_kwargs = {
                    "KeyConditionExpression": Key(key["hash"]).eq(data["hash"])
                    & Key(key["range"]).between(data["range"][0], data["range"][1])
                }
            elif key["operator"] == "le":
                query_kwargs = {
                    "KeyConditionExpression": Key(key["hash"]).eq(data["hash"])
                    & Key(key["range"]).lte(data["range"])
                }
            elif key["operator"] == "eq":
                query_kwargs = {
                    "KeyConditionExpression": Key(key["hash"]).eq(data["hash"])
                    & Key(key["range"]).eq(data["range"])
                }

        else:
            query_kwargs = {"KeyConditionExpression": Key(key).eq(data)}

        if index_name:
            query_kwargs["IndexName"] = index_name

        items = []
        key = None
        while True:
            if key:
                query_kwargs["ExclusiveStartKey"] = key

            response = self.table.query(**query_kwargs)
            items.extend(response.get("Items", []))
            key = response.get("LastEvaluatedKey")

            if not key:
                break

        return {"Items": items, "ExclusiveStartKey": None}

    def add(self, data):
        if self.validator:
            if not self.validator.validate(data):
                raise SchemaError(self.validator.errors)

        data = json.loads(json.dumps(data, default=json_encoder), parse_float=Decimal)

        return self.table.put_item(Item=data)

    def update(self, data, key):
        item = self.get_item(key)

        if item:
            item.update(data)
            return self.table.put_item(
                Item=json.loads(
                    json.dumps(item, default=json_encoder), parse_float=Decimal
                )
            )

    def delete(self, key: dict):
        return self.table.delete_item(Key=key)

    def batch_add(self, data):
        if self.validator:
            for x in data:
                if not self.validator.validate(x):
                    raise SchemaError(self.validator.errors)

        with self.table.batch_writer() as batch:
            for r in data:
                r = json.loads(json.dumps(r, default=json_encoder), parse_float=Decimal)
                batch.put_item(Item=r)

        return True

    def get_all(self):
        final_result = []
        scan_kwargs = {}
        done = False
        start_key = None

        while not done:
            if start_key:
                scan_kwargs["ExclusiveStartKey"] = start_key
            response = self.table.scan(**scan_kwargs)
            final_result.extend(response.get("Items", []))
            start_key = response.get("LastEvaluatedKey", None)
            done = start_key is None

        return final_result

    def get_all_filtered_items(self, data: any, key: str, operator: str = "in") -> list:
        """Get all filtered items from DynamoDB Table.

        :param data: query data
        :param key: query field
        :return: list [...items...]
        """

        final_result = list()
        scan_kwargs = {}
        done = False
        start_key = None
        if operator == "in":
            scan_kwargs["FilterExpression"] = Attr(key).is_in(data)

        while not done:
            if start_key:
                scan_kwargs["ExclusiveStartKey"] = start_key
            response = self.table.scan(**scan_kwargs)
            final_result.extend(response.get("Items", []))
            start_key = response.get("LastEvaluatedKey", None)
            done = start_key is None

        return final_result

    def query(self, query_kwargs):
        items = []
        key = None
        while True:
            if key:
                query_kwargs["ExclusiveStartKey"] = key

            response = self.table.query(**query_kwargs)
            items.extend(response.get("Items", []))
            key = response.get("LastEvaluatedKey")

            if not key:
                break
        return items
