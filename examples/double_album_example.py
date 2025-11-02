#!/usr/bin/env python3
"""Example: Creating a double album j-card."""

from cardgen import load_config
from cardgen.api.builder import (
    create_double_album_card,
    render_cards_to_pdf,
)
from cardgen.config import Theme

# Load configuration (assumes config.toml exists in current directory)
config = load_config()

# Option 1: Basic double album card
print("Creating basic double album card...")
card = create_double_album_card(
    url1="album/FIRST_ALBUM_ID",
    url2="album/SECOND_ALBUM_ID",
    config=config,
)

# Render to PDF
render_cards_to_pdf([card], "double_album_basic.pdf", dpi=600)
print("✓ Saved to double_album_basic.pdf")

# Option 2: Double album with gradient
print("\nCreating double album with gradient...")
card_gradient = create_double_album_card(
    url1="album/FIRST_ALBUM_ID",
    url2="album/SECOND_ALBUM_ID",
    config=config,
    theme=Theme(
        use_gradient=True,
        gradient_indices=(0, 1),  # Use most frequent colors
    )
)

render_cards_to_pdf([card_gradient], "double_album_gradient.pdf", dpi=600)
print("✓ Saved to double_album_gradient.pdf")

# Option 3: Double album with Dolby logo
print("\nCreating double album with Dolby logo...")
card_dolby = create_double_album_card(
    url1="album/FIRST_ALBUM_ID",
    url2="album/SECOND_ALBUM_ID",
    config=config,
    theme=Theme(
        dolby_logo=True,
    )
)

render_cards_to_pdf([card_dolby], "double_album_dolby.pdf", dpi=600)
print("✓ Saved to double_album_dolby.pdf")

# Option 4: Double album with custom settings
print("\nCreating double album with custom settings...")
card_custom = create_double_album_card(
    url1="album/FIRST_ALBUM_ID",
    url2="album/SECOND_ALBUM_ID",
    config=config,
    theme=Theme(
        use_gradient=True,
        dolby_logo=True,
        tape_length=120,  # C120 tape
        cover_art_mode="fullscale",
        cover_art_align="center",
    )
)

render_cards_to_pdf([card_custom], "double_album_custom.pdf", dpi=720)
print("✓ Saved to double_album_custom.pdf")

print("\n✓ All examples completed!")
print("\nCLI Usage:")
print("  cardgen album 'album/ID1,album/ID2' -o output.pdf")
print("  cardgen album 'album/ID1,album/ID2' --gradient --dolby-logo")
