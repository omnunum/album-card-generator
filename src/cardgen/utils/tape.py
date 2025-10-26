"""Cassette tape utilities for side calculation."""

from dataclasses import dataclass

from cardgen.api.models import Track


@dataclass
class TapeSide:
    """Represents one side of a cassette tape."""

    side: str  # "A" or "B"
    tracks: list[Track]
    total_duration: int  # seconds
    max_duration: int  # seconds (per side capacity)

    @property
    def remaining_time(self) -> int:
        """Get remaining time on this side in seconds."""
        return self.max_duration - self.total_duration


def assign_tape_sides(tracks: list[Track], tape_length_minutes: int = 90) -> int:
    """
    Assign side="A" or side="B" to each track based on tape capacity.

    Fills Side A with as many complete tracks as possible, then assigns the rest to Side B.
    Tracks are never split - they must fit entirely on one side.

    Modifies tracks in place by setting their .side attribute.

    Args:
        tracks: List of tracks to assign sides to.
        tape_length_minutes: Total tape length in minutes (default: 90 for C90 cassette).

    Returns:
        Side capacity in seconds (tape_length_minutes * 60 / 2).

    Raises:
        ValueError: If any single track exceeds side capacity or total duration exceeds tape capacity.
    """
    # Calculate capacity per side (in seconds)
    side_capacity_seconds = (tape_length_minutes * 60) // 2

    # Check if album fits on tape
    total_duration = sum(track.duration for track in tracks)
    tape_capacity = tape_length_minutes * 60
    if total_duration > tape_capacity:
        raise ValueError(
            f"Album duration ({total_duration // 60}:{total_duration % 60:02d}) "
            f"exceeds tape capacity ({tape_length_minutes} minutes)"
        )

    # Check if any single track exceeds side capacity
    for track in tracks:
        if track.duration > side_capacity_seconds:
            raise ValueError(
                f"Track {track.track_number} '{track.title}' ({track.format_duration()}) "
                f"exceeds single side capacity ({side_capacity_seconds // 60} minutes)"
            )

    # Assign Side A to as many tracks as possible
    side_a_duration = 0
    split_index = 0

    for i, track in enumerate(tracks):
        if side_a_duration + track.duration <= side_capacity_seconds:
            track.side = "A"
            side_a_duration += track.duration
            split_index = i + 1
        else:
            # Can't fit this track on Side A, stop here
            break

    # Assign Side B to remaining tracks
    side_b_duration = 0
    for i in range(split_index, len(tracks)):
        tracks[i].side = "B"
        side_b_duration += tracks[i].duration

    # Validate Side B doesn't exceed capacity
    if side_b_duration > side_capacity_seconds:
        raise ValueError(
            f"Side B duration ({side_b_duration // 60}:{side_b_duration % 60:02d}) "
            f"exceeds side capacity ({side_capacity_seconds // 60} minutes). "
            "Try a longer tape or reorder tracks."
        )

    return side_capacity_seconds


def split_tracks_by_tape_sides(tracks: list[Track], tape_length_minutes: int = 90) -> tuple[TapeSide, TapeSide]:
    """
    Split tracks into Side A and Side B based on tape capacity.

    DEPRECATED: Use assign_tape_sides() instead for simpler code.
    This function is kept for backward compatibility.

    Fills Side A with as many complete tracks as possible, then moves to Side B.
    Tracks are never split - they must fit entirely on one side.

    Args:
        tracks: List of tracks to split.
        tape_length_minutes: Total tape length in minutes (default: 90 for C90 cassette).

    Returns:
        Tuple of (side_a, side_b) TapeSide objects.

    Raises:
        ValueError: If any single track exceeds side capacity or total duration exceeds tape capacity.
    """
    # Use new function to assign sides
    side_capacity_seconds = assign_tape_sides(tracks, tape_length_minutes)

    # Build TapeSide objects from assigned tracks
    side_a_tracks = [t for t in tracks if t.side == "A"]
    side_b_tracks = [t for t in tracks if t.side == "B"]

    side_a_duration = sum(t.duration for t in side_a_tracks)
    side_b_duration = sum(t.duration for t in side_b_tracks)

    side_a = TapeSide(side="A", tracks=side_a_tracks, total_duration=side_a_duration, max_duration=side_capacity_seconds)
    side_b = TapeSide(side="B", tracks=side_b_tracks, total_duration=side_b_duration, max_duration=side_capacity_seconds)

    return side_a, side_b
