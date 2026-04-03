"""
    StorageS3AWS class
"""
# pylint: disable=E0401,R0801
import boto3
from app.classes.storage import Storage


class StorageS3AWS (Storage):
    """
        Class to connect to S3 AWS
    Args:
        Storage (class): Parent class
    """

    def __init__(self, config):
        """
            Connection to S3 AWS

        Args:
            config (class): basic information required to connect to S3 AWS
        """
        self.config = config
        self.bucket = self.config.bucket
        try:
            self.auth = {}
            self.auth['aws_access_key_id'] = self.config.auth['aws_access_key_id']
            self.auth['aws_secret_access_key'] = self.config.auth['aws_secret_access_key']
            self.auth['region_name'] = self.config.auth['region_name']
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.auth['aws_access_key_id'],
                aws_secret_access_key=self.auth['aws_secret_access_key'],
                region_name=self.auth['region_name']
            )
        except KeyError:
            self.s3 = boto3.client('s3')

    def put_object(self, file_data, file_key):
        """
            Put an object in S3
        Args:
            file_data (bytes): Data of the file to upload
            file_key (str): Destination path of the file in S3

        Returns:
            _type_: _description_
        """
        bucket = self.config.bucket
        return self.s3.put_object(Bucket=bucket, Key=file_key, Body=file_data)

    def get_object(self, file_key):
        """
            Get an object from S3

        Args:
            file_key (str): Path of the file in S3

        Returns:
            bytes: Content of the file
        """
        bucket = self.config.bucket
        return self.s3.get_object(Bucket=bucket, Key=file_key)
