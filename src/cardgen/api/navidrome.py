"""Navidrome API client wrapper."""

from urllib.parse import urlparse

import libopensonic

from cardgen.api.models import Album, Playlist, Track
from cardgen.config import NavidromeConfig


class NavidromeClient:
    """Client for interacting with Navidrome server via OpenSubsonic API."""

    def __init__(self, config: NavidromeConfig) -> None:
        """
        Initialize Navidrome client.

        Args:
            config: Navidrome configuration with URL and credentials.
        """
        self.config = config
        parsed = urlparse(config.url)

        # Extract base URL without port
        base_url = f"{parsed.scheme}://{parsed.hostname}"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        self.conn = libopensonic.Connection(
            base_url=base_url,
            username=config.username,
            password=config.password,
            port=port,
        )

    def get_album(self, album_id: str) -> Album:
        """
        Fetch album by ID.

        Args:
            album_id: Album ID from Navidrome.

        Returns:
            Album object with all metadata and tracks.

        Raises:
            Exception: If album not found or API error occurs.
        """
        # Get album metadata (returns AlbumID3 dataclass)
        album_data = self.conn.get_album(album_id)

        # Extract track information
        tracks: list[Track] = []
        if album_data.song:
            for song in album_data.song:
                track = Track(
                    title=song.title or "Unknown",
                    duration=song.duration or 0,
                    track_number=song.track or 0,
                    artist=song.artist,
                    album=song.album,
                )
                tracks.append(track)

        # Sort tracks by track number
        tracks.sort(key=lambda t: t.track_number)

        # Get cover art
        cover_art_id = album_data.cover_art or album_id
        cover_art = self.get_cover_art(cover_art_id)

        # Get label from record_labels if available
        label = None
        if album_data.record_labels and len(album_data.record_labels) > 0:
            label = album_data.record_labels[0].name if hasattr(album_data.record_labels[0], 'name') else str(album_data.record_labels[0])

        return Album(
            id=album_data.id,
            title=album_data.name or "Unknown Album",
            artist=album_data.artist or "Unknown Artist",
            year=album_data.year,
            genre=album_data.genre,
            label=label,
            cover_art=cover_art,
            tracks=tracks,
        )

    def get_playlist(self, playlist_id: str) -> Playlist:
        """
        Fetch playlist by ID.

        Args:
            playlist_id: Playlist ID from Navidrome.

        Returns:
            Playlist object with all metadata and tracks.

        Raises:
            Exception: If playlist not found or API error occurs.
        """
        # Get playlist with songs
        playlist_data = self.conn.get_playlist(playlist_id)

        # Extract track information
        tracks: list[Track] = []
        if "entry" in playlist_data:
            for idx, song in enumerate(playlist_data["entry"], start=1):
                track = Track(
                    title=song.get("title", "Unknown"),
                    duration=song.get("duration", 0),
                    track_number=idx,  # Use position in playlist
                    artist=song.get("artist"),
                    album=song.get("album"),
                )
                tracks.append(track)

        # Get cover art if available
        cover_art = None
        if "coverArt" in playlist_data:
            try:
                cover_art = self.get_cover_art(playlist_data["coverArt"])
            except Exception:
                # If playlist cover art fails, try first track's album art
                if tracks and tracks[0].album:
                    try:
                        cover_art = self.get_cover_art(playlist_data["entry"][0].get("coverArt"))
                    except Exception:
                        pass

        return Playlist(
            id=playlist_data["id"],
            name=playlist_data.get("name", "Unknown Playlist"),
            comment=playlist_data.get("comment"),
            owner=playlist_data.get("owner", "Unknown"),
            public=playlist_data.get("public", False),
            song_count=playlist_data.get("songCount", len(tracks)),
            duration=playlist_data.get("duration", 0),
            created=playlist_data.get("created", ""),
            changed=playlist_data.get("changed", ""),
            cover_art=cover_art,
            tracks=tracks,
        )

    def get_cover_art(self, cover_id: str, size: int = 600) -> bytes:
        """
        Fetch cover art by ID.

        Args:
            cover_id: Cover art ID from Navidrome.
            size: Desired size in pixels (server may return different size).

        Returns:
            Raw image bytes (JPEG or PNG).

        Raises:
            Exception: If cover art not found or API error occurs.
        """
        response = self.conn.get_cover_art(cover_id, size=size)
        return response.content

    @staticmethod
    def extract_id_from_url(url: str) -> tuple[str, str]:
        """
        Extract album or playlist ID from Navidrome web UI URL or path.

        Args:
            url: Full URL from Navidrome web interface, or just "album/ID" or "playlist/ID".

        Returns:
            Tuple of (type, id) where type is 'album' or 'playlist'.

        Raises:
            ValueError: If URL format is not recognized.

        Examples:
            >>> NavidromeClient.extract_id_from_url("http://server/app/#/album/123")
            ('album', '123')
            >>> NavidromeClient.extract_id_from_url("album/123")
            ('album', '123')
            >>> NavidromeClient.extract_id_from_url("playlist/456")
            ('playlist', '456')
        """
        # Check if it's a simple path format first
        if "/" in url and not url.startswith("http"):
            parts = url.split("/")
            if len(parts) >= 2:
                resource_type = parts[0]
                resource_id = parts[1]

                if resource_type in ("album", "playlist"):
                    return resource_type, resource_id

        # Parse URL fragment (after #)
        if "#/" in url:
            fragment = url.split("#/", 1)[1]
            parts = fragment.split("/")

            if len(parts) >= 2:
                resource_type = parts[0]
                resource_id = parts[1]

                if resource_type in ("album", "playlist"):
                    return resource_type, resource_id

        raise ValueError(
            f"Could not extract album or playlist ID from: {url}\n"
            "Expected format: album/ID, playlist/ID, or http://server/app/#/album/ID"
        )
