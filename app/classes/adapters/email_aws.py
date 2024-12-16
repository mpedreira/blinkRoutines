#!/usr/bin/env python3
# pylint: disable=C0301
# -*- coding: utf-8 -*-
"""Module for static configuration of Claroty"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.classes.email import Email


class EmailAWS (Email):
    """Module for static configuration of Claroty"""

    def __init__(self, config):
        """Inicialization of config module"""
        self.config = config
        self.auth = {}
        self.endpoints = {}
        self.payload = {}
        self.auth['SMTP_PASSWORD'] = self.config.auth['SMTP_PASSWORD']
        self.auth['SMTP_USERNAME'] = self.config.auth['SMTP_USERNAME']
        self.auth['TELEGRAM_API'] = self.config.auth['TELEGRAM_API']
        self.endpoints['SMTP_HOST'] = self.config.endpoints['SMTP_HOST']
        self.endpoints['SMTP_PORT'] = self.config.endpoints['SMTP_PORT']
        self.endpoints['TELEGRAM_BASEPATH'] = self.config.endpoints['TELEGRAM_BASEPATH']
        self.payload['MAIL_FROM'] = self.config.payload['MAIL_FROM']
        self.payload['SMTP_CHARSET'] = self.config.payload['SMTP_CHARSET']

    def set_destination(self, destination):
        """
            Establish the destination of the email
        Args:
            destination (str): Destination of the email

        Returns:
            bool: Returns True
        """
        self.payload['MAIL_TO'] = destination
        return True

    def send_email(self, subject, body):
        """
        Send email to the user
        Args:
            body (str): Body of the email
        """
        msg = MIMEMultipart()
        msg['From'] = self.payload['MAIL_FROM']
        msg['To'] = self.payload['MAIL_TO']
        msg['Subject'] = subject
        # plain = self.__html_to_text__(body)
        msg.attach(MIMEText(body, 'html'))
        # msg.attach(MIMEText(plain, 'plain'))
        smtp_instance = smtplib.SMTP(
            self.endpoints['SMTP_HOST'], self.endpoints['SMTP_PORT'])
        smtp_instance.starttls()
        smtp_instance.login(
            self.auth['SMTP_USERNAME'], self.auth['SMTP_PASSWORD'])
        text = msg.as_string()
        result = smtp_instance.sendmail(self.payload['MAIL_FROM'],
                                        self.payload['MAIL_TO'], text)
        smtp_instance.quit()
        return self.__get_response_to_request__(result)

    def __get_response_to_request__(self, smtp_response):
        """
        Args:
            http_instance (class): this is the class used for the http request

        Returns:
            list: returns a json file with the status_code of the server, if the
            response is ok or not and the response of the server. If the response is
            not a json, it returns the text without format
        """
        result = {}
        result['status_code'] = self.__get_status_code__(smtp_response)
        result['is_ok'] = self.__is_ok_response__(smtp_response)
        result['response'] = smtp_response
        return result

    def __is_ok_response__(self, response):
        return len(response) == 0

    def __get_status_code__(self, response):
        if self.__is_ok_response__(response):
            return 200
        return 500

    def __html_to_text__(self, html):
        plain_text = ""
        in_tag = False

        for char in html:
            if char == "<":  # Comienza una etiqueta
                in_tag = True
            elif char == ">":  # Termina una etiqueta
                in_tag = False
            elif not in_tag:  # Si no está dentro de una etiqueta, añadir el texto
                plain_text += char

        return plain_text.strip()
