"""
    DatabaseDynamoAWS class
"""
# pylint: disable=E0401

import boto3
from app.classes.database import Database


class DatabaseDynamoAWS (Database):
    """
        DatabaseDynamoAWS class
    Args:
        Database (class): Superclass
    """

    def __init__(self, config):
        """
            Connection to Dynamo AWS

        Args:
            config (class): basic information required to connect to Dynamo AWS
        """
        self.config = config
        self.table = self.config.table
        try:
            self.auth = {}
            self.auth['aws_access_key_id'] = self.config.auth['aws_access_key_id']
            self.auth['aws_secret_access_key'] = self.config.auth['aws_secret_access_key']
            self.auth['region_name'] = self.config.auth['region_name']
            self.db = boto3.resource(
                'dynamodb',
                aws_access_key_id=self.auth['aws_access_key_id'],
                aws_secret_access_key=self.auth['aws_secret_access_key'],
                region_name=self.auth['region_name']
            )
        except KeyError:
            self.db = boto3.resource('dynamodb')

    def put_item(self, item):
        """
            Put item in DynamoDB

        Args:
            item (dict): item to put in the table

        Returns:
            dict: response of the DynamoDB
        """
        table = self.db.Table(self.table)
        response = table.put_item(Item=item)
        return self.__get_response_to_request__(response)

    def get_item(self, key):
        """
            Get item in DynamoDB

        Args:
            key (dict): key to get the item in the table

        Returns:
            dict: response of the DynamoDB
        """
        table = self.db.Table(self.table)
        response = table.get_item(Key=key)
        return self.__get_response_to_request__(response)

    def update_item(self, key, update_expression,
                    expression_attribute_values, return_values="UPDATED_NEW"):
        """
            Update item in DynamoDB

        Args:
            key (dict): key to get the item in the table
            update_expression (str): expression to update the item
            expression_attribute_values (dict): values to update the item

        Returns:
            dict: response of the DynamoDB
        """
        table = self.db.Table(self.table)
        response = table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues=return_values
        )
        return self.__get_response_to_request__(response)

    def query(self, key_condition_expression, limit=100):
        """
            Query items in DynamoDB

        Args:
            key_condition_expression (str): expression to query the items
            expression_attribute_values (dict): values to query the items

        Returns:
            dict: response of the DynamoDB
        """
        table = self.db.Table(self.table)
        response = table.query(
            KeyConditionExpression=key_condition_expression,
            Limit=limit
        )
        return self.__get_response_to_request__(response)

    def scan(self, key_condition_expression, limit=100):
        """
            Query items in DynamoDB

        Args:
            key_condition_expression (str): expression to query the items
            expression_attribute_values (dict): values to query the items

        Returns:
            dict: response of the DynamoDB
        """
        table = self.db.Table(self.table)
        response = table.scan(
            FilterExpression=key_condition_expression,
            Limit=limit
        )
        return self.__get_response_to_request__(response)

    def __get_response_to_request__(self, response):
        """
        Args:
            http_instance (class): this is the class used for the http request

        Returns:
            list: returns a json file with the status_code of the server, if the
            response is ok or not and the response of the server. If the response is
            not a json, it returns the text without format
        """
        result = {}

        result['status_code'] = response['ResponseMetadata']['HTTPStatusCode']
        result['is_ok'] = self.__is_ok__(result['status_code'])
        result['response'] = response

        return result

    def __is_ok__(self, status_code):
        """
        Args:
            status_code (int): status code of the server

        Returns:
            bool: returns True if the status code is 2XX, False otherwise
        """
        return status_code == 200
