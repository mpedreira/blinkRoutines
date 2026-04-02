from datetime import datetime, timedelta
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigStatic
from app.classes.adapters.telegram_api import TelegramApi
from app.classes.adapters.http_request_standard import HttpRequestStandard

config_instance = ConfigStatic()
blink_instance = BlinkAPI(config_instance)
blink_instance.__set_token__()
blink_instance.get_server()
response = blink_instance.send_2fa(2FA_CODE)
