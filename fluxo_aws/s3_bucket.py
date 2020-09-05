import boto3
from botocore.exceptions import ClientError


class S3Bucket:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")

    def upload_file(self, file_name, object_name=None):
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        try:
            response = self.s3_client.upload_file(
                file_name, self.bucket_name, object_name
            )
        except ClientError as e:
            # logging.error(e)
            return False
        return True

    def download_file(self, object_name, file_name=None):
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
            response = self.s3_client.upload_file(
                file_name, self.bucket_name, object_name
            )
        except ClientError as e:
            # logging.error(e)
            return False
        return True

    def download_fileobj(self, object_name, file_name):
        """Download a fileObject from S3 bucket

        :param object_name: S3 object name. If not specified then file_name is used
        :param file_name: File object
        :return: True if file was uploaded, else False
        """

        # If S3 file_name was not specified, use object_name
        if file_name is None:
            file_name = object_name

        # Download the file
        try:
            response = self.s3_client.download_fileobj(
                self.bucket_name, object_name, file_name
            )
        except ClientError as e:
            # logging.error(e)
            return False
        return True

    def create_presigned_url(self, object_name, action="get_object", expiration=3600):
        """Generate a presigned URL to share an S3 object

        :param object_name: string
        :param action: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """

        # Generate a presigned URL for the S3 object
        try:
            response = self.s3_client.generate_presigned_url(
                action,
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
        except ClientError as e:
            # logging.error(e)
            return None

        # The response contains the presigned URL
        return response
