"""API clients for music servers."""

from cardgen.api.builder import (
    create_card,
    create_card_from_album,
    render_cards_to_pdf,
)
from cardgen.api.models import Album, Playlist, Track
from cardgen.api.navidrome import NavidromeClient

__all__ = [
    "Album",
    "Playlist",
    "Track",
    "NavidromeClient",
    "create_card",
    "create_card_from_album",
    "render_cards_to_pdf",
]
