"""
This file contains the endpoint to build and play the podcast queue via Spotify.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.spotify_api import SpotifyAPI

router = APIRouter()


@router.post("")
def play_music(play: bool = True):
    """
        Clears the queue playlist and refills it with new/unplayed podcast
        episodes based on the configured shows and time windows.

        When play=true (default), also starts playback on the configured
        Spotify device (requires an active Spotify session on the device).

        When play=false, only prepares the playlist so it can be played
        manually from the Spotify app at any time.

    Args:
        play (bool): Whether to start playback immediately. Defaults to True.

    Returns:
        dict: Result with is_ok, episodes_added and status_code
    """
    config_instance = ConfigAWS()
    return SpotifyAPI(config_instance).build_and_play_queue(play=play)
