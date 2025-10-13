#!/usr/bin/env python3
"""Debug rendering to see what's happening with Side B."""

from pathlib import Path
from PIL import Image
import io

from cardgen.api.models import Album, Track
from cardgen.config import DefaultThemeConfig
from cardgen.design.cards import JCard4Panel
from cardgen.design.themes import DefaultTheme

# Create simple test with fewer tracks
tracks = [
    Track(title="Track 1", duration=300, track_number=1, artist="Test Artist"),  # 5:00
    Track(title="Track 2", duration=300, track_number=2, artist="Test Artist"),  # 5:00
    Track(title="Track 3", duration=300, track_number=3, artist="Test Artist"),  # 5:00
    Track(title="Track 4", duration=300, track_number=4, artist="Test Artist"),  # 5:00
    Track(title="Track 5", duration=300, track_number=5, artist="Test Artist"),  # 5:00
]
# Total: 25 minutes - should split roughly in half on C90

# Create cover art
img = Image.new('RGB', (600, 600), color=(100, 100, 200))
cover_art_buffer = io.BytesIO()
img.save(cover_art_buffer, format='PNG')
cover_art_bytes = cover_art_buffer.getvalue()

album = Album(
    id="test-001",
    title="Test",
    artist="Test Artist",
    year=2025,
    genre="Test",
    label="Test",
    cover_art=cover_art_bytes,
    tracks=tracks
)

theme = DefaultTheme(DefaultThemeConfig())
card = JCard4Panel(album, theme, tape_length_minutes=90)

print(f"Side A: {len(card.side_a.tracks)} tracks - {[t.track_number for t in card.side_a.tracks]}")
print(f"Side B: {len(card.side_b.tracks)} tracks - {[t.track_number for t in card.side_b.tracks]}")

# Check the data being passed to render
sections = card.get_sections()
tracklist_section = [s for s in sections if s.content_type == 'tracklist'][0]

print(f"\nTracklist section data keys: {tracklist_section.data.keys()}")
print(f"Side A in data: {tracklist_section.data.get('side_a') is not None}")
print(f"Side B in data: {tracklist_section.data.get('side_b') is not None}")

if tracklist_section.data.get('side_b'):
    print(f"Side B has tracks: {len(tracklist_section.data['side_b'].tracks)}")
