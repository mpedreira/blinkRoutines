"""
    PersonDetectorAzure - Azure Face API adapter for face detection.
"""
# pylint: disable=E0401,R0801
import io
from azure.ai.vision.face import FaceAdministrationClient, FaceClient
from azure.ai.vision.face.models import FaceRecognitionModel, FaceDetectionModel
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from app.classes.person_detector import PersonDetector, UNKNOWN_PERSON, FACE_CONFIDENCE_THRESHOLD

# Azure confidence is in 0-1 range; convert threshold to that scale
_AZURE_CONFIDENCE_THRESHOLD = FACE_CONFIDENCE_THRESHOLD / 100


class PersonDetectorAzure(PersonDetector):
    """
    Adapter that uses Azure Face API PersonGroups for face detection and registration.

    Args:
        PersonDetector (class): Parent class
    """

    def __init__(self, config):
        """
        Init method for PersonDetectorAzure.

        Args:
            config (class): ConfigAzure instance with Azure credentials
        """
        super().__init__(config)
        key = config.auth.get('azure_face_key', '')
        endpoint = config.endpoints.get('AZURE_FACE', '')
        if not key or not endpoint:
            raise ValueError(
                "Azure Face credentials not configured. "
                "Set azure_face_key and azure_face_endpoint in config.ini."
            )
        self.person_group_id = getattr(config, 'azure_person_group_id', 'familia')
        credential = AzureKeyCredential(key)
        self.admin_client = FaceAdministrationClient(
            endpoint=endpoint, credential=credential
        )
        self.face_client = FaceClient(endpoint=endpoint, credential=credential)
        self._ensure_person_group()

    def _ensure_person_group(self):
        """Creates the PersonGroup if it does not exist."""
        try:
            self.admin_client.get_person_group(self.person_group_id)
        except HttpResponseError as err:
            if err.status_code == 404:
                self.admin_client.create_person_group(
                    self.person_group_id,
                    name=self.person_group_id,
                    recognition_model=FaceRecognitionModel.RECOGNITION04,
                )
            else:
                raise

    def _find_person_id(self, person_name):
        """Returns the Azure person_id for a given name, or None if not found."""
        try:
            persons = list(
                self.admin_client.get_person_group_persons(self.person_group_id)
            )
        except HttpResponseError:
            return None
        for person in persons:
            if person.name == person_name:
                return person.person_id
        return None

    def register_face(self, image_bytes, person_name):
        """
            Registers a face in the Azure PersonGroup.
            Creates the Person entry if it does not exist, adds the face,
            then triggers group training automatically.

        Args:
            image_bytes (bytes): Image with the face to register
            person_name (str): Name to associate with the face

        Returns:
            dict: Result with 'is_ok', 'faces_indexed' and 'person_name'
        """
        try:
            person_id = self._find_person_id(person_name)
            if person_id is None:
                person = self.admin_client.create_person_group_person(
                    self.person_group_id,
                    name=person_name,
                )
                person_id = person.person_id

            self.admin_client.add_face_from_stream_to_person_group_person(
                self.person_group_id,
                person_id,
                image_content=io.BytesIO(image_bytes),
                detection_model=FaceDetectionModel.DETECTION03,
            )

            poller = self.admin_client.begin_train_person_group(self.person_group_id)
            poller.result()

            return {'is_ok': True, 'faces_indexed': 1, 'person_name': person_name}
        except HttpResponseError as err:
            return {
                'is_ok': False,
                'faces_indexed': 0,
                'person_name': person_name,
                'error': str(err),
            }

    def list_faces(self):
        """
            Lists all Person entries in the PersonGroup.

        Returns:
            dict: Result with 'is_ok', 'faces' list and 'face_count'.
                  Each face entry has 'face_id', 'person_name' and 'persisted_face_count'.
        """
        try:
            persons = list(
                self.admin_client.get_person_group_persons(self.person_group_id)
            )
        except HttpResponseError as err:
            return {'is_ok': False, 'faces': [], 'face_count': 0, 'error': str(err)}

        faces = [
            {
                'face_id': str(person.person_id),
                'person_name': person.name,
                'confidence': 0.0,
                'persisted_face_count': len(person.persisted_face_ids or []),
            }
            for person in persons
        ]
        return {'is_ok': True, 'faces': faces, 'face_count': len(faces)}

    def detect_faces(self, image_bytes):
        """
            Detects and identifies faces in an image using the Azure PersonGroup.

        Args:
            image_bytes (bytes): Image to analyze

        Returns:
            list: List of dicts with 'name' and 'confidence' for each face found.
                  Unknown or low-confidence faces appear as UNKNOWN_PERSON.
        """
        try:
            detected = self.face_client.detect(
                image_content=io.BytesIO(image_bytes),
                detection_model=FaceDetectionModel.DETECTION03,
                recognition_model=FaceRecognitionModel.RECOGNITION04,
                return_face_id=True,
            )
        except HttpResponseError:
            return []

        if not detected:
            return []

        face_ids = [f.face_id for f in detected]

        try:
            identify_results = self.face_client.identify_from_person_group(
                face_ids=face_ids,
                person_group_id=self.person_group_id,
                max_num_of_candidates_returned=1,
                confidence_threshold=_AZURE_CONFIDENCE_THRESHOLD,
            )
        except HttpResponseError:
            return [{'name': UNKNOWN_PERSON, 'confidence': 0}] * len(face_ids)

        # Cache person_id -> name to avoid redundant API calls
        person_cache: dict = {}
        results = []
        for result in identify_results:
            if result.candidates:
                best = result.candidates[0]
                confidence = round(best.confidence * 100, 2)
                person_id_str = str(best.person_id)
                if person_id_str not in person_cache:
                    try:
                        person = self.admin_client.get_person_group_person(
                            self.person_group_id, best.person_id
                        )
                        person_cache[person_id_str] = person.name
                    except HttpResponseError:
                        person_cache[person_id_str] = UNKNOWN_PERSON
                results.append({'name': person_cache[person_id_str], 'confidence': confidence})
            else:
                results.append({'name': UNKNOWN_PERSON, 'confidence': 0})

        return results

    def delete_face(self, person_name):
        """
            Deletes all Person entries registered under the given person name.

        Args:
            person_name (str): Name of the person to remove

        Returns:
            dict: Result with 'is_ok', 'deleted_count' and 'person_name'
        """
        try:
            persons = list(
                self.admin_client.get_person_group_persons(self.person_group_id)
            )
        except HttpResponseError as err:
            return {'is_ok': False, 'deleted_count': 0, 'error': str(err)}

        matching = [p for p in persons if p.name == person_name]
        if not matching:
            return {
                'is_ok': False,
                'deleted_count': 0,
                'error': f"No faces found for '{person_name}'",
            }

        deleted = 0
        for person in matching:
            try:
                self.admin_client.delete_person_group_person(
                    self.person_group_id, person.person_id
                )
                deleted += 1
            except HttpResponseError:
                pass

        return {'is_ok': True, 'deleted_count': deleted, 'person_name': person_name}
