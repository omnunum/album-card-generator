#!/usr/bin/env python3
"""
Simple Example: Single Card with Custom Font

This is the simplest way to create a custom j-card programmatically.
"""

from cardgen import Theme, create_card, load_config, render_cards_to_pdf
from cardgen.design import JCard4Panel

# Load config (for Navidrome credentials)
config = load_config()

# Create a card with custom font
card = create_card(
    "album/022k7B9XoO1he20FsXGUuh/show",  # Replace with your album URL
    config,
    JCard4Panel,
    Theme(
        title_google_font="Orbitron",
        title_font_weight=800,
        use_gradient=True,
        title_font_size=20,
        artist_font_size=30,
        artist_google_font="Orbitron",
        artist_font_weight=400,
        dolby_logo=True,
        label_logo="https://kagi.com/proxy/gb1qta628tre1.png?c=TklOzPjLPioJ5YMJT75bSqbOvNy81tkBsxLuoTItbsNXavdMe7R68XGmq94gzX0y"
    ),
)

# Render to PDF
render_cards_to_pdf([card], "my_card.pdf")

print("✓ Card saved to: my_card.pdf")
