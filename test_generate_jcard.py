#!/usr/bin/env python3
"""Test j-card generation with sample album data."""

from pathlib import Path

from cardgen.api.models import Album, Track
from cardgen.config import DefaultThemeConfig
from cardgen.design.cards import JCard4Panel
from cardgen.design.themes import DefaultTheme
from cardgen.render import PDFRenderer

# Create sample album - 72 minutes total, tracks between 2-7 minutes
# Designed to fill both sides of a C90 tape (45 min per side)
tracks = [
    Track(title="Opening Sequence", duration=245, track_number=1, artist="Test Artist"),      # 4:05
    Track(title="Electric Dreams", duration=387, track_number=2, artist="Test Artist"),       # 6:27
    Track(title="Midnight Run", duration=198, track_number=3, artist="Test Artist"),          # 3:18
    Track(title="Neon Lights", duration=423, track_number=4, artist="Test Artist"),           # 7:03
    Track(title="City Streets", duration=312, track_number=5, artist="Test Artist"),          # 5:12
    Track(title="Lost Highway", duration=267, track_number=6, artist="Test Artist"),          # 4:27
    Track(title="Stargazer", duration=354, track_number=7, artist="Test Artist"),             # 5:54
    Track(title="Golden Hour", duration=411, track_number=8, artist="Test Artist"),           # 6:51
    Track(title="Interlude", duration=142, track_number=9, artist="Test Artist"),             # 2:22
    Track(title="Retrograde", duration=389, track_number=10, artist="Test Artist"),           # 6:29
    Track(title="Final Chapter", duration=298, track_number=11, artist="Test Artist"),        # 4:58
    Track(title="Echoes", duration=366, track_number=12, artist="Test Artist"),               # 6:06
    Track(title="Farewell", duration=528, track_number=13, artist="Test Artist"),             # 8:48
]
# Total: 4320 seconds = 72:00 minutes

# Create a simple cover art (solid color PNG)
from PIL import Image
import io

# Create a 600x600 gradient image
img = Image.new('RGB', (600, 600))
pixels = img.load()
for y in range(600):
    for x in range(600):
        # Create a blue gradient
        pixels[x, y] = (int(x / 600 * 100), int(y / 600 * 150), 200)

# Save to bytes
cover_art_buffer = io.BytesIO()
img.save(cover_art_buffer, format='PNG')
cover_art_bytes = cover_art_buffer.getvalue()

# Create album
album = Album(
    id="test-album-001",
    title="Neon Nights",
    artist="Synthwave Collective",
    year=2025,
    genre="Synthwave / Electronic",
    label="Retro Records",
    cover_art=cover_art_bytes,
    tracks=tracks
)

print(f"Creating j-card for: {album.artist} - {album.title}")
print(f"Total duration: {album.format_total_duration()}")
print(f"Tracks: {len(tracks)}")

# Create theme
theme_config = DefaultThemeConfig()
theme = DefaultTheme(theme_config)

# Create card with 90-minute tape
card = JCard4Panel(album, theme, tape_length_minutes=90)

print(f"\nSide A: {len(card.side_a.tracks)} tracks ({card.side_a.total_duration // 60}:{card.side_a.total_duration % 60:02d})")
print(f"Side B: {len(card.side_b.tracks)} tracks ({card.side_b.total_duration // 60}:{card.side_b.total_duration % 60:02d})")

# Render PDF
output_path = Path("test_jcard.pdf")
renderer = PDFRenderer(dpi=600, include_crop_marks=True, page_size="letter")

print(f"\nGenerating PDF: {output_path}")
renderer.render_card(card, output_path)

print(f"✓ J-card generated successfully: {output_path}")
print("\nYou can now open test_jcard.pdf to see the result!")
