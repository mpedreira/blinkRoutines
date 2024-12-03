"""
    Class for controlling the Telegram API.
"""
import json
from app.classes.adapters.http_request_standard import HttpRequestStandard
from app.classes.telegram import Telegram

# pylint: disable=C0301,R0903,E0401,R0801


class TelegramApi(Telegram):
    """
    Class for controlling the Telegram API.
    Args:
        Telegram (class): Parent class
    """

    def __prepare_http_request__(self):
        """
            Prepare the http request for the Telegram API.
        Returns:
            dict: basic payload for the http request
        """
        payload = {}
        payload['config'] = self.config
        payload['headers'] = ''
        payload['data'] = ''
        payload['auth'] = ''
        payload['timeout'] = self.config.timeout
        return payload

    def send_message(self, message, channel):
        """
            Sends the message to a channel in Telegram.

        Args:
            message (str): Message send to the channel
            channel (str): Channel id where the message is going to be send

        Returns:
            dict: Response of the Telegram API
        """
        token = self.config.auth['TELEGRAM_API']
        basepath = self.config.endpoints['TELEGRAM_BASEPATH']
        payload = self.__prepare_http_request__()
        endpoint = {}
        endpoint[
            'uri'] = basepath + token + "/sendMessage" + "?chat_id=" + channel + "&text=" + message
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        return json.loads(http_instance.response.text)

    def send_image_from_bytes(self, image, channel):
        """
            Sends a image to a channel in Telegram.

        Args:
            image (str): Path to the image
            channel (str): Channel id where the message is going to be send

        Returns:
            dict: Response of the Telegram API
        """
        token = self.config.auth['TELEGRAM_API']
        basepath = self.config.endpoints['TELEGRAM_BASEPATH']
        payload = self.__prepare_http_request__()
        endpoint = {}
        endpoint['uri'] = basepath + token + "/sendPhoto"
        endpoint['certificate'] = False
        payload['files'] = {'photo': image}
        payload['data'] = {'chat_id': channel}
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        return json.loads(http_instance.response.text)

    def send_video(self, video, channel):
        """
            Sends a image to a channel in Telegram.

        Args:
            video (bytes): Downloaded video
            channel (str): Channel id where the message is going to be send

        Returns:
            dict: Response of the Telegram API
        """
        token = self.config.auth['TELEGRAM_API']
        basepath = self.config.endpoints['TELEGRAM_BASEPATH']
        payload = self.__prepare_http_request__()
        endpoint = {}
        endpoint['uri'] = basepath + token + "/sendVideo"
        endpoint['certificate'] = False
        payload['files'] = {'video': video}
        payload['data'] = {'chat_id': channel}
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        return self.__get_response_to_request__(http_instance)

    def send_image(self, image, channel):
        """
            Sends a image to a channel in Telegram.

        Args:
            image (str): Path to the image
            channel (str): Channel id where the message is going to be send

        Returns:
            dict: Response of the Telegram API
        """
        token = self.config.auth['TELEGRAM_API']
        basepath = self.config.endpoints['TELEGRAM_BASEPATH']
        payload = self.__prepare_http_request__()
        endpoint = {}
        endpoint['uri'] = basepath + token + "/sendPhoto"
        endpoint['certificate'] = False
        with open(image, 'rb') as img_file:
            payload['files'] = {'photo': img_file}
        payload['data'] = {'chat_id': channel}
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        return self.__get_response_to_request__(http_instance)

    def __get_response_to_request__(self, http_instance):
        """
        Args:
            http_instance (class): this is the class used for the http request

        Returns:
            list: returns a json file with the status_code of the server, if the
            response is ok or not and the response of the server. If the response is
            not a json, it returns the text without format
        """
        result = {}
        result['status_code'] = http_instance.response.status_code
        result['is_ok'] = http_instance.is_ok_response()
        try:
            result['response'] = json.loads(http_instance.response.text)
        except json.decoder.JSONDecodeError:
            result['response'] = {"message": http_instance.response.text}
        return result
