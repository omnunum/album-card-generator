"""API clients for music servers."""

from cardgen.api.models import Album, Playlist, Track
from cardgen.api.navidrome import NavidromeClient

__all__ = ["Album", "Playlist", "Track", "NavidromeClient"]
