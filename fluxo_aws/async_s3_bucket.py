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
