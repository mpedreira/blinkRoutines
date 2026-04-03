"""Script for manually sending a 2FA code to complete Blink OAuth login."""
import sys
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS


def main():
    """Send a 2FA code passed as a command-line argument."""
    if len(sys.argv) < 2:
        print("Usage: python3 get_2fa.py <2fa_code>")
        sys.exit(1)
    mfa_code = sys.argv[1]
    config_instance = ConfigAWS()
    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    response = blink_instance.send_2fa(mfa_code)
    print(response)


if __name__ == '__main__':
    main()
