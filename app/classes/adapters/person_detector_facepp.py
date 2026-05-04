"""
    PersonDetectorFacePP - Face++ (Face Plus Plus) adapter for face detection.

    Uses the Face++ v3 REST API directly via requests (no official SDK needed).
    Key concepts:
      - FaceSet : collection of face_tokens (equivalent to Rekognition Collection /
                  Azure PersonGroup).  Identified by a user-defined outer_id.
      - face_token: opaque id returned by /detect.  Expires in 72 h unless added
                    to a FaceSet.
      - user_id   : custom label attached to a face_token via /face/setuserdata,
                    used as the person name.
"""
# pylint: disable=E0401,R0801
import requests
from app.classes.person_detector import PersonDetector, UNKNOWN_PERSON, FACE_CONFIDENCE_THRESHOLD

_BASE_TIMEOUT = 30
_MAX_FACES_PER_PAGE = 100  # maximum allowed by Face++ faceset/getdetail


class PersonDetectorFacePP(PersonDetector):
    """
    Adapter that uses the Face++ v3 REST API for face registration and detection.

    Args:
        PersonDetector (class): Parent class
    """

    def __init__(self, config):
        """
        Init method for PersonDetectorFacePP.

        Args:
            config (class): ConfigFacePP instance with Face++ credentials
        """
        super().__init__(config)
        self.api_key = config.auth.get('facepp_api_key', '')
        self.api_secret = config.auth.get('facepp_api_secret', '')
        self.base_url = config.endpoints.get('FACEPP', 'https://api-us.faceplusplus.com')
        self.outer_id = getattr(config, 'facepp_faceset_outer_id', 'familia')

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Face++ credentials not configured. "
                "Set facepp_api_key and facepp_api_secret in config.ini."
            )
        self._ensure_faceset()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(self, path, data=None, files=None):
        """POST to the Face++ API and return the parsed JSON response."""
        url = f"{self.base_url}{path}"
        payload = {'api_key': self.api_key, 'api_secret': self.api_secret}
        if data:
            payload.update(data)
        try:
            resp = requests.post(url, data=payload, files=files, timeout=_BASE_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as err:
            return {'error_message': str(err)}

    def _image_file(self, image_bytes):
        """Build the multipart files dict for image upload."""
        return {'image_file': ('image.jpg', image_bytes, 'image/jpeg')}

    def _ensure_faceset(self):
        """Creates the FaceSet if it does not exist yet."""
        result = self._request(
            '/facepp/v3/faceset/getdetail', {'outer_id': self.outer_id}
        )
        if 'error_message' in result:
            # Any error here means the faceset doesn't exist — create it
            self._request('/facepp/v3/faceset/create', {
                'outer_id': self.outer_id,
                'display_name': self.outer_id,
            })

    def _get_all_face_tokens(self):
        """
        Returns all face_tokens stored in the FaceSet (handles pagination).

        Returns:
            list[str]: List of face_token strings
        """
        tokens = []
        start = 0
        while True:
            result = self._request('/facepp/v3/faceset/getdetail', {
                'outer_id': self.outer_id,
                'start': start,
            })
            if 'error_message' in result:
                break
            page_tokens = result.get('face_tokens', [])
            tokens.extend(page_tokens)
            if len(page_tokens) < _MAX_FACES_PER_PAGE:
                break
            start += _MAX_FACES_PER_PAGE
        return tokens

    def _get_face_user_id(self, face_token):
        """Returns the user_id associated with a face_token, or None."""
        result = self._request('/facepp/v3/face/getdetail', {'face_token': face_token})
        return result.get('user_id') or None

    # ------------------------------------------------------------------
    # PersonDetector interface
    # ------------------------------------------------------------------

    def register_face(self, image_bytes, person_name):
        """
            Detects the largest face in the image, attaches person_name as user_id,
            and adds the face_token to the FaceSet.

        Args:
            image_bytes (bytes): Image with the face to register
            person_name (str): Name to associate with the face

        Returns:
            dict: Result with 'is_ok', 'faces_indexed' and 'person_name'
        """
        detect_result = self._request(
            '/facepp/v3/detect', files=self._image_file(image_bytes)
        )
        if 'error_message' in detect_result:
            return {
                'is_ok': False,
                'faces_indexed': 0,
                'person_name': person_name,
                'error': detect_result['error_message'],
            }

        faces = detect_result.get('faces', [])
        if not faces:
            return {
                'is_ok': False,
                'faces_indexed': 0,
                'person_name': person_name,
                'error': 'No face detected in the image',
            }

        # Use the first (largest) detected face
        face_token = faces[0]['face_token']

        # Attach the person name as user_id
        self._request('/facepp/v3/face/setuserdata', {
            'face_token': face_token,
            'user_id': person_name,
        })

        # Add to FaceSet
        add_result = self._request('/facepp/v3/faceset/addface', {
            'outer_id': self.outer_id,
            'face_tokens': face_token,
        })
        if 'error_message' in add_result:
            return {
                'is_ok': False,
                'faces_indexed': 0,
                'person_name': person_name,
                'error': add_result['error_message'],
            }

        return {'is_ok': True, 'faces_indexed': 1, 'person_name': person_name}

    def list_faces(self):
        """
            Lists all registered faces in the FaceSet with their person names.

        Returns:
            dict: Result with 'is_ok', 'faces' list and 'face_count'.
                  Each entry has 'face_id' (face_token) and 'person_name'.
        """
        tokens = self._get_all_face_tokens()
        faces = []
        for token in tokens:
            user_id = self._get_face_user_id(token)
            faces.append({
                'face_id': token,
                'person_name': user_id or UNKNOWN_PERSON,
                'confidence': 0.0,
            })
        return {'is_ok': True, 'faces': faces, 'face_count': len(faces)}

    def detect_faces(self, image_bytes):
        """
            Detects all faces in the image and identifies each against the FaceSet.

        Args:
            image_bytes (bytes): Image to analyze

        Returns:
            list: List of dicts with 'name' and 'confidence' for each face found.
                  Unrecognised faces appear as UNKNOWN_PERSON.
        """
        detect_result = self._request(
            '/facepp/v3/detect', files=self._image_file(image_bytes)
        )
        if 'error_message' in detect_result:
            return []

        faces = detect_result.get('faces', [])
        if not faces:
            return []

        results = []
        for face in faces:
            face_token = face['face_token']
            search_result = self._request('/facepp/v3/search', {
                'face_token': face_token,
                'outer_id': self.outer_id,
                'return_result_count': 1,
            })

            if 'error_message' in search_result or not search_result.get('results'):
                results.append({'name': UNKNOWN_PERSON, 'confidence': 0})
                continue

            best = search_result['results'][0]
            confidence = round(best.get('confidence', 0), 2)
            person_name = best.get('user_id') or UNKNOWN_PERSON

            if confidence < FACE_CONFIDENCE_THRESHOLD:
                person_name = UNKNOWN_PERSON

            results.append({'name': person_name, 'confidence': confidence})

        return results

    def delete_face(self, person_name):
        """
            Removes all face_tokens associated with person_name from the FaceSet.

        Args:
            person_name (str): Name of the person to remove

        Returns:
            dict: Result with 'is_ok', 'deleted_count' and 'person_name'
        """
        tokens = self._get_all_face_tokens()
        if not tokens:
            return {
                'is_ok': False,
                'deleted_count': 0,
                'error': f"No faces found for '{person_name}'",
            }

        matching = [t for t in tokens if self._get_face_user_id(t) == person_name]
        if not matching:
            return {
                'is_ok': False,
                'deleted_count': 0,
                'error': f"No faces found for '{person_name}'",
            }

        # Face++ allows up to 5 face_tokens per removeface call
        removed = 0
        chunk_size = 5
        for i in range(0, len(matching), chunk_size):
            chunk = matching[i:i + chunk_size]
            result = self._request('/facepp/v3/faceset/removeface', {
                'outer_id': self.outer_id,
                'face_tokens': ','.join(chunk),
            })
            if 'error_message' not in result:
                removed += result.get('face_removed', len(chunk))

        return {'is_ok': True, 'deleted_count': removed, 'person_name': person_name}
