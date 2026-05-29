"""Constants for the Blink Routines integration."""

DOMAIN = "blink_routines"

CONF_API_URL = "api_url"
CONF_AGENTS_API_URL = "agents_api_url"
CONF_NETWORK_ID = "network_id"
CONF_TELEGRAM_CHANNEL = "telegram_channel_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_LAST_VIDEO_WAIT_SECONDS = "last_video_wait_seconds"
CONF_MIN_CONFIDENCE = "min_confidence"

DEFAULT_SCAN_INTERVAL = 30  # minutes
DEFAULT_LAST_VIDEO_WAIT_SECONDS = 30
DEFAULT_MIN_CONFIDENCE = 70
DEFAULT_AGENTS_API_URL = ""

SERVICE_DETECT_VIDEO_FACES = "detect_video_faces"
SERVICE_REGISTER_VIDEO_FACE = "register_video_face"

ATTR_CAM_NAME = "cam_name"
ATTR_PERSON_NAME = "person_name"
ATTR_SAMPLE_FPS = "sample_fps"
ATTR_MIN_CONFIDENCE = "min_confidence"

EVENT_VIDEO_FACE_DETECTED = "blink_routines_video_face_detected"
EVENT_VIDEO_FACE_REGISTERED = "blink_routines_video_face_registered"
EVENT_VIDEO_FACE_ERROR = "blink_routines_video_face_error"

EVENT_THUMB_FACE_DETECTED = "blink_routines_thumb_face_detected"
EVENT_THUMB_FACE_REGISTERED = "blink_routines_thumb_face_registered"
