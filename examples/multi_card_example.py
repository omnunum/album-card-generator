#!/usr/bin/env python3
"""
Example: Creating Multiple Cards with Custom Styling

This example demonstrates how to use the Python API to create
multiple j-cards with different styling and render them to a
single multi-page PDF.

Requirements:
- Configure your Navidrome credentials in config.toml
- Replace the example album IDs with your own
"""

from cardgen import Theme, create_card_from_album, load_config, render_cards_to_pdf, NavidromeClient, JCard4Panel, JCard5Panel, AlbumArt

# Load base configuration (contains Navidrome credentials)
config = load_config()
client = NavidromeClient(config.navidrome)

# =============================================================================
# Card 1: Orbitron font with gradient background
# =============================================================================
album1 = client.get_album("your-album-id-1")  # Replace with your album ID
art1 = AlbumArt(album1.cover_art)

card1 = create_card_from_album(
    album1,
    art1,
    JCard5Panel,
    Theme(
        # Google Fonts for title and artist
        title_google_font="Orbitron",
        title_font_weight=900,  # Black weight for bold impact
        artist_google_font="Roboto",
        artist_font_weight=400,  # Regular weight
        # Gradient background extracted from album art
        use_gradient=True,
        gradient_indices=(0, 1),  # Use two most frequent colors
        # Dolby NR logo on spine
        dolby_logo=True,
    ),
)

# =============================================================================
# Card 2: Custom solid colors, fullscale cover art
# =============================================================================
album2 = client.get_album("your-album-id-2")  # Replace with your album ID
art2 = AlbumArt(album2.cover_art)

card2 = create_card_from_album(
    album2,
    art2,
    JCard4Panel,
    Theme(
        # Custom solid color scheme
        background_color=(0.95, 0.95, 0.95),  # Light gray
        text_color=(0.1, 0.1, 0.1),  # Dark gray/black
        accent_color=(0.3, 0.3, 0.3),  # Medium gray
        # Fullscale cover art (fills full height with crop)
        cover_art_mode="fullscale",
        cover_art_align="left",  # Align to left edge
        # Custom tape length (C60 = 30 minutes per side)
        tape_length=60,
    ),
)

# =============================================================================
# Card 3: Different Google Fonts, aggressive character compression
# =============================================================================
album3 = client.get_album("your-album-id-3")  # Replace with your album ID
art3 = AlbumArt(album3.cover_art)

card3 = create_card_from_album(
    album3,
    art3,
    JCard4Panel,
    Theme(
        # Different font pairing
        title_google_font="Bebas Neue",
        title_font_weight=400,
        artist_google_font="Open Sans",
        artist_font_weight=300,  # Light weight
        # Tighter character spacing for long track titles
        min_track_title_char_spacing=-1.5,  # More aggressive compression
        # Wrap overflowing track titles instead of truncating
        track_title_overflow="wrap",
    ),
)

# =============================================================================
# Card 4: Minimal config - uses all defaults
# =============================================================================
# This demonstrates that you don't need to specify everything.
# Only override what you want to change!
album4 = client.get_album("your-album-id-4")  # Replace with your album ID
art4 = AlbumArt(album4.cover_art)

card4 = create_card_from_album(album4, art4, JCard5Panel)  # All defaults

# =============================================================================
# Render all cards to a single multi-page PDF
# =============================================================================
# Cards are stacked vertically, 2 per page
# Page 1: Card 1 (top) + Card 2 (bottom)
# Page 2: Card 3 (top) + Card 4 (bottom)

render_cards_to_pdf(
    cards=[card1, card2, card3, card4],
    output_path="my_custom_cards.pdf",
    dpi=720,  # Higher quality
    include_crop_marks=True,  # Include cutting/folding guides
    page_size="letter",  # US Letter (8.5" x 11")
    config=config,
)

print("✓ Created multi-page PDF: my_custom_cards.pdf")
print(f"  - {len([card1, card2, card3, card4])} cards on {2} pages")
print("  - Each card has custom styling")
