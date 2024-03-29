from botocore.exceptions import ClientError
import aioboto3


class AsyncS3Bucket:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name

    async def __aenter__(self):
        self.s3_client = await aioboto3.client("s3").__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.s3_client.__aexit__(exc_type, exc, tb)

    async def upload_file(self, file_name: str, object_name=None, ExtraArgs=None):
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        await self.s3_client.upload_file(
            file_name, self.bucket_name, object_name, ExtraArgs=ExtraArgs
        )

        return True

    async def download_file(self, object_name: str, file_name=None):
        """Download a file from S3 bucket

        :param file_name: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 file_name was not specified, use object_name
        if file_name is None:
            file_name = object_name

        # Download the file
        try:
            response = await self.s3_client.download_file(
                self.bucket_name, object_name, file_name
            )
        except ClientError:
            return None
        return response

    async def download_fileobj(self, object_name, file_name: str):
        """Download a fileObject from S3 bucket

        :param object_name: S3 object name. If not specified then file_name is used
        :param file_name: File object
        :return: True if file was uploaded, else False
        """

        # If S3 file_name was not specified, use object_name
        if file_name is None:
            file_name = object_name

        await self.s3_client.download_fileobj(self.bucket_name, object_name, file_name)

        return True

    async def create_presigned_url(
        self, object_name, action="get_object", expiration=3600
    ):
        """Generate a presigned URL to share an S3 object

        :param object_name: string
        :param action: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """

        # Generate a presigned URL for the S3 object
        try:
            response = await self.s3_client.generate_presigned_url(
                action,
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
        except ClientError:
            return None

        # The response contains the presigned URL
        return response

    async def generate_presigned_post(
        self, file_name: str, ExpiresIn=360, Fields=None, Conditions=None
    ):
        response = await self.s3_client.generate_presigned_post(
            Bucket=self.bucket_name,
            Key=file_name,
            ExpiresIn=ExpiresIn,
            Fields=Fields,
            Conditions=Conditions,
        )
        return response

    async def delete_object(self, key, bucket_name=None):
        response = await self.s3_client.delete_object(
            Bucket=bucket_name or self.bucket_name, Key=key
        )
        return response

    async def list_objects(self, prefix=None, bucket_name=None):
        final_result = []
        query_kwargs = {
            "Bucket": bucket_name or self.bucket_name,
            "MaxKeys": 1000,
            "Prefix": prefix,
        }
        query_kwargs = {k: v for k, v in query_kwargs.items() if v}
        done = False
        continuation_token = None

        while not done:
            if continuation_token:
                query_kwargs["ContinuationToken"] = continuation_token
            response = await self.s3_client.list_objects_v2(**query_kwargs)
            final_result.extend(response.get("Contents", []))
            continuation_token = response.get("ContinuationToken", None)
            done = continuation_token is None

        return final_result

    async def move_object(self, source, dest, bucket_name=None):
        await self.s3_client.copy_object(
            Bucket=bucket_name or self.bucket_name,
            CopySource=f"/{bucket_name or self.bucket_name}/{source}",
            Key=dest,
        )

        await self.s3_client.delete_object(
            Bucket=bucket_name or self.bucket_name,
            Key=source,
        )
