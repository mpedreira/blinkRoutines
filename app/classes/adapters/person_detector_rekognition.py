"""
    PersonDetectorRekognition - Amazon Rekognition adapter for face detection.
"""
# pylint: disable=E0401,R0801
import boto3
from botocore.exceptions import ClientError
from app.classes.person_detector import PersonDetector, UNKNOWN_PERSON


class PersonDetectorRekognition(PersonDetector):
    """
    Adapter that uses Amazon Rekognition Face Collections for person detection.

    Args:
        PersonDetector (class): Parent class
    """

    def __init__(self, config):
        """
        Init method for PersonDetectorRekognition.

        Args:
            config (class): Basic configuration with AWS credentials
        """
        super().__init__(config)
        key_id = config.auth.get('aws_access_key_id', '')
        secret = config.auth.get('aws_secret_access_key', '')
        region = config.auth.get('region_name', 'us-east-1')
        if not key_id or not secret:
            raise ValueError(
                "AWS credentials not configured. "
                "Set aws_access_key_id and aws_secret_access_key in config.ini."
            )
        self.client = boto3.client(
            'rekognition',
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            region_name=region
        )
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the face collection if it does not exist."""
        try:
            self.client.create_collection(CollectionId=self.collection_id)
        except ClientError as err:
            if err.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                raise

    def detect_faces(self, image_bytes):
        """
            Searches for known faces in the image using the Rekognition collection.

        Args:
            image_bytes (bytes): Image to analyze

        Returns:
            list: List of dicts with 'name' and 'confidence' for each face found.
                  Unknown faces appear as UNKNOWN_PERSON.
        """
        try:
            response = self.client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['DEFAULT']
            )
        except ClientError:
            return []

        face_count = len(response.get('FaceDetails', []))
        if face_count == 0:
            return []

        try:
            search_response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                FaceMatchThreshold=80,
                MaxFaces=10
            )
        except ClientError:
            return [{'name': UNKNOWN_PERSON, 'confidence': 0}] * face_count

        # FaceMatches contains all collection candidates for the same detected
        # face, sorted by similarity descending. Keep only the best match per
        # detected face to avoid reporting sibling lookalikes as separate people.
        best_match = search_response.get('FaceMatches', [])[:1]
        matched_names = []
        for match in best_match:
            matched_names.append({
                'name': match['Face']['ExternalImageId'],
                'confidence': round(match['Face']['Confidence'], 2)
            })

        unmatched = face_count - len(matched_names)
        for _ in range(unmatched):
            matched_names.append({'name': UNKNOWN_PERSON, 'confidence': 0})

        return matched_names

    def register_face(self, image_bytes, person_name):
        """
            Indexes a face into the Rekognition collection.

        Args:
            image_bytes (bytes): Image with the face to register
            person_name (str): Name to associate with the face

        Returns:
            dict: Result with 'is_ok', 'faces_indexed' and 'person_name'
        """
        try:
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=person_name,
                DetectionAttributes=['DEFAULT']
            )
        except ClientError as err:
            return {
                'is_ok': False,
                'faces_indexed': 0,
                'person_name': person_name,
                'error': str(err)
            }

        indexed = len(response.get('FaceRecords', []))
        return {
            'is_ok': indexed > 0,
            'faces_indexed': indexed,
            'person_name': person_name
        }

    def detect_vacuum(self, image_bytes, min_confidence=70):
        """
        Uses Rekognition label detection to decide whether the moving
        object in the image is a robot vacuum cleaner.

        Args:
            image_bytes (bytes): Thumbnail to analyse.
            min_confidence (float): Minimum label confidence (0-100).

        Returns:
            bool: True if a vacuum / robot cleaner label is found above the
                  confidence threshold, False otherwise.
        """
        # Labels that appear when the Roborock Q80 is visible in frame
        # (calibrated empirically: absent in baseline shots, present with robot)
        vacuum_labels = {"electrical device", "switch"}
        try:
            response = self.client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=20,
                MinConfidence=min_confidence,
            )
        except ClientError:
            return False

        detected = {
            label['Name'].lower()
            for label in response.get('Labels', [])
        }
        return bool(detected & vacuum_labels)

    def list_faces(self):
        """
            Lists all registered faces in the collection.

        Returns:
            dict: Result with 'is_ok', 'faces' list and 'face_count'
        """
        try:
            response = self.client.list_faces(
                CollectionId=self.collection_id,
                MaxResults=100
            )
        except ClientError as err:
            return {
                'is_ok': False,
                'faces': [],
                'face_count': 0,
                'error': str(err)
            }

        faces = []
        for face in response.get('FaceRecords', response.get('Faces', [])):
            faces.append({
                'face_id': face.get('FaceId', ''),
                'person_name': face.get('ExternalImageId', UNKNOWN_PERSON),
                'confidence': round(face.get('Confidence', 0), 2)
            })
        return {
            'is_ok': True,
            'faces': faces,
            'face_count': len(faces)
        }

    def delete_face(self, person_name):
        """
            Deletes all faces registered under the given person name.

        Args:
            person_name (str): Name of the person to remove

        Returns:
            dict: Result with 'is_ok' and 'deleted_count'
        """
        try:
            all_faces = self.client.list_faces(
                CollectionId=self.collection_id,
                MaxResults=100
            )
        except ClientError as err:
            return {'is_ok': False, 'deleted_count': 0, 'error': str(err)}

        face_ids = [
            f['FaceId']
            for f in all_faces.get('Faces', [])
            if f.get('ExternalImageId') == person_name
        ]

        if not face_ids:
            return {'is_ok': False, 'deleted_count': 0,
                    'error': f"No faces found for '{person_name}'"}

        try:
            self.client.delete_faces(
                CollectionId=self.collection_id,
                FaceIds=face_ids
            )
        except ClientError as err:
            return {'is_ok': False, 'deleted_count': 0, 'error': str(err)}

        return {'is_ok': True, 'deleted_count': len(face_ids), 'person_name': person_name}
