"""Album card generator for Navidrome."""

__version__ = "0.1.0"

# High-level Python API
from cardgen.api import (
    create_card,
    create_card_from_album,
    render_cards_to_pdf,
)
from cardgen.config import Theme, load_config

__all__ = [
    "Theme",
    "create_card",
    "create_card_from_album",
    "render_cards_to_pdf",
    "load_config",
]
