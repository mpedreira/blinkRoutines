"""Module for music playback via Spotify."""
# pylint: disable=R0903


class Spotify:
    """Base port class for Spotify integration."""

    def __init__(self, config):
        """
        Init method for Spotify.

        Args:
            config (class): Basic configuration with Spotify credentials
        """
        self.config = config

    def build_and_play_queue(self):  # pylint: disable=W0613
        """
            Build podcast queue from configured sources and start playback.

        Returns:
            dict: Result with is_ok and episodes_added
        """
        return {}
