"""Album card generator for Navidrome."""

__version__ = "0.1.0"

# High-level Python API
from cardgen.api import (
    create_card,
    create_card_from_album,
    create_double_album_card,
    create_double_album_card_from_albums,
    render_cards_to_pdf,
)
from cardgen.api.navidrome import NavidromeClient
from cardgen.api.models import Album, Track
from cardgen.config import Theme, load_config
from cardgen.design.cards.jcard_4panel import JCard4Panel
from cardgen.design.cards.jcard_5panel import JCard5Panel
from cardgen.utils.album_art import AlbumArt

__all__ = [
    "Theme",
    "create_card",
    "create_card_from_album",
    "create_double_album_card",
    "create_double_album_card_from_albums",
    "render_cards_to_pdf",
    "load_config",
    "NavidromeClient",
    "Album",
    "Track",
    "JCard4Panel",
    "JCard5Panel",
    "AlbumArt",
]
