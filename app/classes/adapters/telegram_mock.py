"""
    Class for controlling the Telegram API.
"""
import json
from app.classes.telegram import Telegram


# pylint: disable=C0301,R0903,E0401


class TelegramMock (Telegram):
    """
    Class for controlling the Telegram API.
    Args:
        Telegram (class): Parent class
    """

    def send_message(self, message, channel):
        """
            Sends the message to a channel in Telegram.

        Args:
            message (str): Message send to the channel
            channel (str): Channel id where the message is going to be send

        Returns:
            dict: Response of the Telegram API
        """
        message = '{"ok":true,"result":{"message_id":54,"from":{"id":302953781,"is_bot":true,"first_name":"Apazon","username":"Apazonbot"},"chat":{"id":-4544363357,"title":"Tests","type":"group","all_members_are_administrators":true},"date":1727087682,"text":"Message."}}'
        return json.loads(message)

    def send_image(self, image, channel):
        """
            Sends a image to a channel in Telegram.

        Args:
            image (str): Path to the image
            channel (str): Channel id where the message is going to be send

        Returns:
            dict: Response of the Telegram API
        """
        message = '{"ok":true,"result":{"message_id":54,"from":{"id":302953781,"is_bot":true,"first_name":"Apazon","username":"Apazonbot"},"chat":{"id":-4544363357,"title":"Tests","type":"group","all_members_are_administrators":true},"date":1727087682,"text":"Message."}}'
        return json.loads(message)
