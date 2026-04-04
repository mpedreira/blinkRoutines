"""
Spotify API adapter for podcast queue management.
Refreshes the queue playlist with new/unplayed episodes and starts playback.
"""
# pylint: disable=E0401,R0801,R0903

from datetime import datetime, timedelta, timezone
import requests as _req
from app.classes.spotify import Spotify

_TOKEN_URL = "https://accounts.spotify.com/api/token"
_API_BASE = "https://api.spotify.com/v1"
_DATE_FORMATS = {'day': '%Y-%m-%d', 'month': '%Y-%m', 'year': '%Y'}


class SpotifyAPI(Spotify):
    """Adapter that uses the Spotify Web API to build and play podcast queues."""

    def __init__(self, config):
        """
        Init method for SpotifyAPI.

        Args:
            config (class): Basic configuration with Spotify credentials
        """
        super().__init__(config)
        self._access_token = None

    def _refresh_token(self):
        """Exchange refresh_token for a fresh access_token."""
        resp = _req.post(_TOKEN_URL, data={
            'grant_type': 'refresh_token',
            'refresh_token': self.config.spotify['refresh_token'],
            'client_id': self.config.spotify['client_id'],
            'client_secret': self.config.spotify['client_secret'],
        }, verify=False, timeout=10)
        self._access_token = resp.json()['access_token']

    def _headers(self, json_content=False):
        """Return auth headers, optionally with Content-Type: application/json."""
        headers = {'Authorization': f'Bearer {self._access_token}'}
        if json_content:
            headers['Content-Type'] = 'application/json'
        return headers

    @staticmethod
    def _parse_release_date(date_str, precision):
        """Parse a Spotify release_date string into a UTC-aware datetime."""
        fmt = _DATE_FORMATS.get(precision, '%Y-%m-%d')
        return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)

    def _get_episode_uri(self, show_id, window_hours):
        """
            Returns the URI of the first unplayed episode within the time window.

        Args:
            show_id (str): Spotify show ID
            window_hours (int|None): Only consider episodes released within this
                                     many hours. None means no time restriction.

        Returns:
            str|None: Spotify episode URI or None if no match found
        """
        resp = _req.get(
            f"{_API_BASE}/shows/{show_id}/episodes",
            headers=self._headers(),
            params={'market': 'ES', 'limit': 10},
            verify=False, timeout=10
        )
        cutoff = (
            datetime.now(timezone.utc) - timedelta(hours=window_hours)
            if window_hours is not None else None
        )
        for episode in resp.json().get('items', []):
            if episode.get('resume_point', {}).get('fully_played'):
                continue
            if cutoff:
                precision = episode.get('release_date_precision', 'day')
                release = self._parse_release_date(
                    episode['release_date'], precision)
                if release < cutoff:
                    continue
            return f"spotify:episode:{episode['id']}"
        return None

    def _clear_playlist(self, playlist_id):
        """Replace all playlist tracks with an empty list."""
        _req.put(
            f"{_API_BASE}/playlists/{playlist_id}/tracks",
            headers=self._headers(json_content=True),
            json={'uris': []},
            verify=False, timeout=10
        )

    def _add_to_playlist(self, playlist_id, uris):
        """Add episode URIs to the playlist. Returns True if successful."""
        resp = _req.post(
            f"{_API_BASE}/playlists/{playlist_id}/tracks",
            headers=self._headers(json_content=True),
            json={'uris': uris},
            verify=False, timeout=10
        )
        return resp.ok

    def _play(self, uris, device_id):
        """Transfer playback to device and start playing the given episode URIs."""
        # Transfer playback to device first (wakes it up if inactive)
        _req.put(
            f"{_API_BASE}/me/player",
            headers=self._headers(json_content=True),
            json={'device_ids': [device_id], 'play': False},
            verify=False, timeout=10
        )
        return _req.put(
            f"{_API_BASE}/me/player/play",
            headers=self._headers(json_content=True),
            params={'device_id': device_id},
            json={'uris': uris},
            verify=False, timeout=10
        )

    def build_and_play_queue(self, play=True):
        """
            Fetches new/unplayed episodes from configured podcasts
            and stores them. Optionally starts playback on the device.

        Args:
            play (bool): Whether to start playback after building the queue.
                         Requires an active Spotify session on the device.

        Returns:
            dict: Result with is_ok, status_code and episodes_added
        """
        self._refresh_token()
        podcasts = self.config.spotify.get('podcasts', [])
        device_id = self.config.spotify['device_id']

        uris = []
        for podcast in podcasts:
            uri = self._get_episode_uri(
                podcast['id'], podcast.get('window_hours'))
            if uri:
                uris.append(uri)

        if not uris:
            return {'is_ok': False, 'episodes_added': 0,
                    'response': 'No new unplayed episodes found'}

        # Persist URIs so play_stored_queue can play them later without rebuilding
        self.config.set_spotify_queue(uris)

        if not play:
            return {'is_ok': True, 'episodes_added': len(uris),
                    'response': 'Queue built and saved. Call play_music?play=true to play.'}

        play_resp = self._play(uris, device_id)
        return {
            'is_ok': play_resp.ok,
            'status_code': play_resp.status_code,
            'episodes_added': len(uris)
        }
