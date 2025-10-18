#!/usr/bin/env python3
"""Test RYM descriptors fetching and rendering."""

from pathlib import Path

from cardgen.api import NavidromeClient
from cardgen.config import load_config
from cardgen.design import create_jcard_5panel
from cardgen.design.themes import DefaultTheme
from cardgen.render import PDFRenderer

# Load configuration
cfg = load_config()

# Initialize Navidrome client
client = NavidromeClient(cfg.navidrome)

# Test with a specific album ID - replace with an album that has RYM descriptors
# You'll need to provide an album ID from your Navidrome instance
album_id = input("Enter album ID to test (e.g., from URL album/xxx): ").strip()

if not album_id:
    print("No album ID provided, exiting.")
    exit(1)

print(f"\nFetching album {album_id}...")
album = client.get_album(album_id)

print(f"\nAlbum: {album.artist} - {album.title}")
print(f"Genres: {album.genres}")
print(f"RYM Descriptors: {album.rym_descriptors}")

if not album.rym_descriptors:
    print("\nWarning: No RYM descriptors found for this album!")
    print("Make sure the album has the 'rym_descriptors' tag in Navidrome.")
else:
    print(f"\nFound {len(album.rym_descriptors)} descriptors:")
    for desc in album.rym_descriptors:
        print(f"  - {desc}")

# Create theme
theme = DefaultTheme(cfg.themes.default)

# Create 5-panel card with genre descriptors panel
print("\nGenerating 5-panel j-card with genre/descriptors panel...")
card = create_jcard_5panel(album, theme, tape_length_minutes=90)

# Render PDF
output_path = Path("test_rym_descriptors.pdf")
renderer = PDFRenderer(dpi=600, include_crop_marks=True, page_size="letter")

print(f"Rendering PDF: {output_path}")
renderer.render_card(card, output_path)

print(f"\n✓ J-card generated successfully: {output_path}")
print("Check the rightmost panel for genre tree and RYM descriptors!")
