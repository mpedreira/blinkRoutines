#!/usr/bin/env python3
# pylint: disable=R0903
# -*- coding: utf-8 -*-
"""Module for person detection"""

UNKNOWN_PERSON = "Otra persona"


class PersonDetector():
    """ Intending of following Hexagonal Architecture, this class is the core for PersonDetector"""

    def __init__(self, config):
        """
        Init method for PersonDetector

        Args:
            config (class): Basic configuration
        """
        self.config = config
        self.collection_id = "familia"

    def detect_faces(self, image_bytes):  # pylint: disable=W0613
        """
            Detects faces in an image and returns who they are.

        Args:
            image_bytes (bytes): Image to analyze

        Returns:
            list: List of dicts with detected person names and confidence
        """
        return []

    def register_face(self, image_bytes, person_name):  # pylint: disable=W0613
        """
            Registers a face in the collection.

        Args:
            image_bytes (bytes): Image with the face to register
            person_name (str): Name of the person

        Returns:
            dict: Result of the registration
        """
        return {}

    def list_faces(self):
        """
            Lists all registered faces in the collection.

        Returns:
            dict: Result with registered faces
        """
        return {}
