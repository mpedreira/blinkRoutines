"""
    Class for controlling the Telegram API.
"""
# pylint: disable=C0301,R0903,E0401,W0613


class Telegram:
    """
    Class for controlling the Telegram API.
    Args:
        Telegram (class): Parent class
    """

    def __init__(self, config):
        """
        Init method for Telegram.

        Args:
            config (class): Basic configuration for Telegram

        """
        self.config = config

    def send_message(self, message, channel):
        """
            Sends the message to a channel in Telegram.

        Args:
            message (str): Message send to the channel
            channel (str): Channel id where the message is going to be send

        Returns:
            dict: Response of the Telegram API
        """
        message = ''
        return message

    def send_image(self, image, channel):
        """
            Sends a image to a channel in Telegram.

        Args:
            image (str): Path to the image
            channel (str): Channel id where the message is going to be send

        Returns:
            dict: Response of the Telegram API
        """
        message = ''
        return message
