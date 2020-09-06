import boto3
from boto3.dynamodb.conditions import Key
from cerberus import Validator
import json
from .json_encoder import json_encoder
from decimal import Decimal
from botocore.exceptions import ClientError


class SchemaError(Exception):
    pass


class DynamodbTable:
    def __init__(self, table_name, schema, hash_key=None, partition_key=None):
        print("boto3.__version__")
        print(boto3.__version__)
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
        """Query Items from DynamoDB Table

        :param data: query data
        :param key: query field
        :param startKey: default=None
        :return: dist object {"Items": [...items...], "ExclusiveStartKey":"...next page start key(if there is next page)..."}
        """

        query_kwargs = {"KeyConditionExpression": Key(key).eq(data)}
        if startKey:
            print("Start Key is passed")
            query_kwargs["ExclusiveStartKey"] = startKey
        else:
            print("Start Key is not passed")
        if index_name:
            query_kwargs["IndexName"] = index_name

        response = self.table.query(**query_kwargs)
        startKey = response.get("LastEvaluatedKey", None)
        if response and "Items" in response:
            return {"Items": response["Items"], "ExclusiveStartKey": startKey}
        else:
            return {"Items": []}

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

    def batch_add(self, data):
        for x in data:
            if not self.validator.validate(x):
                raise SchemaError(self.validator.errors)

        try:
            with self.table.batch_writer() as batch:
                for r in data:
                    r = json.loads(
                        json.dumps(r, default=json_encoder), parse_float=Decimal
                    )
                    batch.put_item(Item=r)

        except ClientError as e:
            print("Unexpected error: %s" % e)
            print("DynamoDB Client Error: %s" % e)
            return False
        except self.client.exceptions.ItemCollectionSizeLimitExceededException as e:
            print("Unexpected error: %s" % e)
            print(
                "DynamoDB Client Error[ItemCollectionSizeLimitExceededException]: %s"
                % e
            )
            return False
        except self.client.exceptions.LimitExceededException as e:
            print("Error[DynamoDB LimitExceededException]: %s" % e)
            return False
        except self.client.exceptions.RequestLimitExceeded as e:
            print("Error[DynamoDB RequestLimitExceeded]: %s" % e)
            return False
        except self.client.exceptions.ProvisionedThroughputExceededException as e:
            print("Error[DynamoDB ProvisionedThroughputExceededException]: %s" % e)
            return False

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
