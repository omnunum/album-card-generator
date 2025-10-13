#!/usr/bin/env python3
"""Test tape side calculation logic."""

from cardgen.api.models import Track
from cardgen.utils.tape import split_tracks_by_tape_sides

# Create sample tracks for testing
tracks = [
    Track(title="Track 1", duration=180, track_number=1, artist="Test Artist"),  # 3:00
    Track(title="Track 2", duration=240, track_number=2, artist="Test Artist"),  # 4:00
    Track(title="Track 3", duration=300, track_number=3, artist="Test Artist"),  # 5:00
    Track(title="Track 4", duration=360, track_number=4, artist="Test Artist"),  # 6:00
    Track(title="Track 5", duration=420, track_number=5, artist="Test Artist"),  # 7:00
    Track(title="Track 6", duration=480, track_number=6, artist="Test Artist"),  # 8:00
    Track(title="Track 7", duration=540, track_number=7, artist="Test Artist"),  # 9:00
    Track(title="Track 8", duration=600, track_number=8, artist="Test Artist"),  # 10:00
]

print("Testing tape side calculation with C90 (45 min per side)...")
print(f"Total album duration: {sum(t.duration for t in tracks) // 60} minutes\n")

try:
    side_a, side_b = split_tracks_by_tape_sides(tracks, tape_length_minutes=90)

    print(f"Side A ({len(side_a.tracks)} tracks):")
    for track in side_a.tracks:
        print(f"  {track.track_number}. {track.title} - {track.format_duration()}")
    print(f"  Total: {side_a.total_duration // 60}:{side_a.total_duration % 60:02d}")
    print(f"  Remaining: {side_a.remaining_time // 60}:{side_a.remaining_time % 60:02d}\n")

    print(f"Side B ({len(side_b.tracks)} tracks):")
    for track in side_b.tracks:
        print(f"  {track.track_number}. {track.title} - {track.format_duration()}")
    print(f"  Total: {side_b.total_duration // 60}:{side_b.total_duration % 60:02d}")
    print(f"  Remaining: {side_b.remaining_time // 60}:{side_b.remaining_time % 60:02d}\n")

    print("✓ Tape side calculation successful!")

except ValueError as e:
    print(f"✗ Error: {e}")
