"""
This file contains the endpoint to play the pre-built podcast queue via Spotify.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.spotify_api import SpotifyAPI

router = APIRouter()


@router.post("")
def play_queue():
    """
        Plays the podcast queue previously built by play_music?play=false.
        Requires an active Spotify session on the configured device.

    Returns:
        dict: Result with is_ok, status_code and episodes_playing
    """
    config_instance = ConfigAWS()
    return SpotifyAPI(config_instance).play_stored_queue()
