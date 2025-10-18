"""Data models for albums, tracks, and playlists."""

from dataclasses import dataclass


@dataclass
class Track:
    """Represents a single track."""

    title: str
    duration: int  # seconds
    track_number: int
    artist: str | None = None
    album: str | None = None

    def format_duration(self) -> str:
        """
        Format duration as MM:SS.

        Returns:
            Formatted duration string.
        """
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"


@dataclass
class Album:
    """Represents an album with metadata and tracks."""

    id: str
    title: str
    artist: str
    year: int | None
    genres: list[str]
    label: str | None
    cover_art: bytes  # Raw image data
    tracks: list[Track]
    rym_descriptors: list[str] | None = None  # RateYourMusic descriptors from custom tags

    def total_duration(self) -> int:
        """
        Calculate total album duration in seconds.

        Returns:
            Total duration in seconds.
        """
        return sum(track.duration for track in self.tracks)

    def format_total_duration(self) -> str:
        """
        Format total duration as HH:MM:SS or MM:SS.

        Returns:
            Formatted duration string.
        """
        total = self.total_duration()
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


@dataclass
class Playlist:
    """Represents a playlist with metadata and tracks."""

    id: str
    name: str
    comment: str | None
    owner: str
    public: bool
    song_count: int
    duration: int  # seconds
    created: str  # ISO format
    changed: str  # ISO format
    cover_art: bytes | None  # Raw image data
    tracks: list[Track]

    def format_duration(self) -> str:
        """
        Format duration as HH:MM:SS or MM:SS.

        Returns:
            Formatted duration string.
        """
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
