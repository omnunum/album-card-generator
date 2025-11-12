#!/usr/bin/env python3
"""
Example: Creating Cards from Manually Constructed Albums

This example shows how to create cards without fetching from Navidrome.
Useful for testing or when you have album data from other sources.
"""

from pathlib import Path

from cardgen import Theme, create_card_from_album, render_cards_to_pdf
from cardgen.api.models import Album, Track
from cardgen.design import JCard4Panel
from cardgen.utils.album_art import AlbumArt

# =============================================================================
# Load cover art from file
# =============================================================================
cover_art_path = Path("cover.jpg")  # Replace with your image file
if not cover_art_path.exists():
    print(f"Error: Cover art file not found: {cover_art_path}")
    print("Please provide a cover.jpg file or update the path")
    exit(1)

with open(cover_art_path, "rb") as f:
    cover_art_bytes = f.read()

# =============================================================================
# Manually create album with tracks
# =============================================================================
tracks = [
    Track(
        title="Opening Sequence",
        duration=245,  # Duration in seconds
        track_number=1,
        artist="Synthwave Collective",
    ),
    Track(
        title="Neon Lights",
        duration=312,
        track_number=2,
        artist="Synthwave Collective",
    ),
    Track(
        title="Midnight Drive",
        duration=298,
        track_number=3,
        artist="Synthwave Collective",
    ),
    Track(
        title="Digital Dreams",
        duration=276,
        track_number=4,
        artist="Synthwave Collective",
    ),
    Track(
        title="Chrome Sunset",
        duration=334,
        track_number=5,
        artist="Synthwave Collective",
    ),
]

album = Album(
    id="manual-001",
    title="Neon Nights",
    artist="Synthwave Collective",
    year=2025,
    genres=["Synthwave", "Electronic", "Retrowave"],
    label="Retro Records",
    cover_art=cover_art_bytes,
    tracks=tracks,
)

# =============================================================================
# Create AlbumArt object
# =============================================================================
album_art = AlbumArt(cover_art_bytes)

# =============================================================================
# Create card with custom styling
# =============================================================================
theme = Theme(
    title_google_font="Orbitron",
    title_font_weight=900,
    artist_google_font="Roboto",
    artist_font_weight=400,
    use_gradient=True,
    tape_length=90,
)

card = create_card_from_album(album, album_art, JCard4Panel, theme)

# =============================================================================
# Render to PDF
# =============================================================================
# Note: Without config parameter, the PDF is saved to the current working directory.
# To use config.output_directory, load config with load_config() and pass config=config.
render_cards_to_pdf([card], "manual_card.pdf", dpi=600)

print("✓ Card created from manual Album object")
print("✓ PDF saved to: manual_card.pdf (in current directory)")
