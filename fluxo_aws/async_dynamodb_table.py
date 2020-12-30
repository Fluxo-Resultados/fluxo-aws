from boto3.dynamodb.conditions import Key, Attr
from cerberus import Validator, TypeDefinition
import json
from .json_encoder import json_encoder
from decimal import Decimal
import warnings
import aioboto3
from .dynamodb_table import SchemaError
from aiofile import async_open
import yaml


class AsyncDynamodbTable:
    def __init__(
        self,
        table_name,
        schema=None,
        hash_key=None,
        partition_key=None,
        schema_path=None,
    ):
        self.table_name = table_name
        self.schema = schema
        self.hash_key = hash_key
        self.partition_key = partition_key
        self.schema_path = schema_path

        if self.schema:
            warnings.warn(
                "schema parameter will be deprecated in favor of schema_path for async file read",
                DeprecationWarning,
            )
            self._build_validator()
        else:
            self.validator = None

    def _build_validator(self):
        self.validator = Validator(self.schema)
        self.validator.types_mapping["integer"] = TypeDefinition(
            "integer", (int, Decimal), (bool,)
        )
        self.validator.types_mapping["float"] = TypeDefinition(
            "float", (float, Decimal), ()
        )
        self.validator.types_mapping["number"] = TypeDefinition(
            "number", (int, float, Decimal), (bool,)
        )

    async def __aenter__(self):
        self.client = await aioboto3.client("dynamodb").__aenter__()
        self.resource = await aioboto3.resource("dynamodb").__aenter__()
        self.table = await self.resource.Table(self.table_name)
        if self.schema_path:
            async with async_open(self.schema_path, "r") as opened_file:
                file_content = await opened_file.read(length=-1)
                self.schema = yaml.safe_load(file_content)
                self._build_validator()

        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.__aexit__(exc_type, exc, tb)
        await self.resource.__aexit__(exc_type, exc, tb)

    async def exists(self, id, hash_key=None):
        key = hash_key or self.hash_key
        try:
            data = await self.table.query(KeyConditionExpression=Key(key).eq(id))
            data = data.get("Items", [])
            if data:
                return True
            else:
                return False
        except self.client.exceptions.ResourceNotFoundException:
            return False

    async def get_by_hash_key(self, id, hash_key=None, index_name=None):
        key = hash_key or self.hash_key
        query_kwargs = {"KeyConditionExpression": Key(key).eq(id)}
        if index_name:
            query_kwargs["IndexName"] = index_name

        try:
            data = await self.table.query(**query_kwargs)
            data = data.get("Items", [])
            return data
        except self.client.exceptions.ResourceNotFoundException:
            return []

    async def get_item(self, data):
        data = await self.table.get_item(Key=data)
        data = data.get("Item", {})
        return data

    async def query_items(self, data, key, startKey=None, index_name=None):
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

            response = await self.table.query(**query_kwargs)
            items.extend(response.get("Items", []))
            key = response.get("LastEvaluatedKey")

            if not key:
                break

        return {"Items": items, "ExclusiveStartKey": None}

    async def add(self, data):
        if self.validator:
            if not self.validator.validate(data):
                raise SchemaError(self.validator.errors)

        data = json.loads(json.dumps(data, default=json_encoder), parse_float=Decimal)

        return await self.table.put_item(Item=data)

    async def update(self, data, key):
        item = await self.get_item(key)

        if item:
            item.update(data)
            return await self.table.put_item(
                Item=json.loads(
                    json.dumps(item, default=json_encoder), parse_float=Decimal
                )
            )

    async def delete(self, key: dict):
        return await self.table.delete_item(Key=key)

    async def batch_add(self, data):
        if self.validator:
            for x in data:
                if not self.validator.validate(x):
                    raise SchemaError(self.validator.errors)

        async with self.table.batch_writer() as batch:
            for r in data:
                r = json.loads(json.dumps(r, default=json_encoder), parse_float=Decimal)
                await batch.put_item(Item=r)

        return True

    async def get_all(self):
        final_result = []
        scan_kwargs = {}
        done = False
        start_key = None

        while not done:
            if start_key:
                scan_kwargs["ExclusiveStartKey"] = start_key
            response = await self.table.scan(**scan_kwargs)
            final_result.extend(response.get("Items", []))
            start_key = response.get("LastEvaluatedKey", None)
            done = start_key is None

        return final_result

    async def get_all_filtered_items(
        self, data: any, key: str, operator: str = "in"
    ) -> list:
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
            response = await self.table.scan(**scan_kwargs)
            final_result.extend(response.get("Items", []))
            start_key = response.get("LastEvaluatedKey", None)
            done = start_key is None

        return final_result

    async def query(self, query_kwargs):
        items = []
        key = None
        while True:
            if key:
                query_kwargs["ExclusiveStartKey"] = key

            response = await self.table.query(**query_kwargs)
            items.extend(response.get("Items", []))
            key = response.get("LastEvaluatedKey")

            if not key:
                break
        return items
