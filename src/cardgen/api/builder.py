"""High-level API for programmatic card creation."""

import logging
from pathlib import Path
from typing import Type

from cardgen.api.models import Album
from cardgen.api.navidrome import NavidromeClient
from cardgen.config import Config, Theme
from cardgen.design import Card
from cardgen.fonts import register_google_font
from cardgen.render import PDFRenderer
from cardgen.utils.album_art import AlbumArt

logger = logging.getLogger(__name__)


def create_card(
    url: str,
    config: Config,
    card_class: Type[Card],
    theme: Theme | None = None,
) -> Card:
    """
    Create a card from a Navidrome album URL with custom styling.

    Args:
        url: Navidrome album URL. Can be:
             - Simple format: "album/abc123"
             - Full URL: "http://server/app/#/album/abc123"
        config: Configuration with Navidrome credentials (from load_config()).
        card_class: Card class to instantiate (e.g., JCard4Panel, JCard5Panel).
        theme: Optional theme configuration. If None, uses Theme() defaults.

    Returns:
        Card object ready to be rendered.

    Raises:
        ValueError: If URL is not an album URL or if configuration is invalid.
        ConnectionError: If unable to connect to Navidrome server.

    Example:
        ```python
        from cardgen import Theme, create_card, load_config
        from cardgen.design import JCard4Panel

        config = load_config()

        # Use defaults
        card1 = create_card("album/abc123", config, JCard4Panel)

        # Custom theme
        card2 = create_card(
            "album/xyz789",
            config,
            JCard4Panel,
            Theme(title_google_font="Orbitron", use_gradient=True)
        )
        ```
    """
    # Use default theme if none provided
    theme = theme or Theme()

    # Initialize Navidrome client
    client = NavidromeClient(config.navidrome)

    # Parse URL to extract album ID
    try:
        resource_type, resource_id = NavidromeClient.extract_id_from_url(url)
    except ValueError as e:
        raise ValueError(f"Invalid URL format: {e}") from e

    if resource_type != "album":
        raise ValueError(
            f"URL is for a {resource_type}, not an album. "
            "Use album URLs only (e.g., 'album/abc123')."
        )

    # Fetch album data from Navidrome
    logger.info(f"Fetching album {resource_id} from Navidrome...")
    try:
        album_data = client.get_album(resource_id)
    except Exception as e:
        raise ConnectionError(f"Failed to fetch album from Navidrome: {e}") from e

    logger.info(f"Fetched: {album_data.artist} - {album_data.title}")

    # Create AlbumArt object
    album_art_obj = AlbumArt(album_data.cover_art)

    # Process theme: Register Google Fonts and update resolved font names
    theme_updates = {}

    if theme.title_google_font:
        logger.info(f"Registering Google Font: {theme.title_google_font} (weight {theme.title_font_weight})")
        font_name = register_google_font(theme.title_google_font, theme.title_font_weight)
        if font_name:
            theme_updates["title_font"] = font_name
            logger.info(f"Registered title font: {font_name}")
        else:
            # Fallback to default bold font
            theme_updates["title_font"] = f"{theme.font_family}-Bold"
            logger.warning(f"Failed to register {theme.title_google_font}, using {theme.font_family}-Bold")

    if theme.artist_google_font:
        logger.info(f"Registering Google Font: {theme.artist_google_font} (weight {theme.artist_font_weight})")
        font_name = register_google_font(theme.artist_google_font, theme.artist_font_weight)
        if font_name:
            theme_updates["artist_font"] = font_name
            logger.info(f"Registered artist font: {font_name}")
        else:
            # Fallback to default font
            theme_updates["artist_font"] = theme.font_family
            logger.warning(f"Failed to register {theme.artist_google_font}, using {theme.font_family}")

    # Process theme: Extract gradient colors if enabled
    if theme.use_gradient:
        logger.info("Extracting color palette from album art...")
        extracted_palette = album_art_obj.get_color_palette(max_colors=3)

        # Select gradient colors based on indices
        gradient_indices = theme.gradient_indices
        try:
            theme_updates["gradient_start"] = extracted_palette[gradient_indices[0]]
            theme_updates["gradient_end"] = extracted_palette[gradient_indices[1]]
            theme_updates["color_palette"] = extracted_palette
            logger.info(
                f"Extracted gradient using colors at indices {gradient_indices[0]} and {gradient_indices[1]}"
            )
        except IndexError:
            logger.warning(
                f"Invalid gradient color indices {gradient_indices}, "
                f"palette only has {len(extracted_palette)} colors. Using first two colors."
            )
            theme_updates["gradient_start"] = extracted_palette[0]
            theme_updates["gradient_end"] = extracted_palette[1]
            theme_updates["color_palette"] = extracted_palette

    # Apply theme updates (if any)
    if theme_updates:
        theme = theme.model_copy(update=theme_updates)

    # Apply dolby logo setting to album
    if theme.dolby_logo:
        album_data.show_dolby_logo = True

    # Instantiate card with processed theme
    card = card_class(album_data, theme, album_art_obj, tape_length_minutes=theme.tape_length)

    logger.info(f"Created {card_class.__name__} for '{album_data.title}'")

    return card


def create_card_from_album(
    album: Album,
    album_art: AlbumArt,
    card_class: Type[Card],
    theme: Theme | None = None,
) -> Card:
    """
    Create a card from Album and AlbumArt objects with custom styling.

    This function is useful when you already have Album data
    (e.g., from a previous fetch or manual construction).

    Args:
        album: Album object with metadata and tracks.
        album_art: AlbumArt object created from cover art bytes.
        card_class: Card class to instantiate (e.g., JCard4Panel, JCard5Panel).
        theme: Optional theme configuration. If None, uses Theme() defaults.

    Returns:
        Card object ready to be rendered.

    Example:
        ```python
        from cardgen.api.models import Album, Track
        from cardgen.utils.album_art import AlbumArt
        from cardgen import Theme, create_card_from_album
        from cardgen.design import JCard4Panel

        # Manually create album
        album = Album(
            id="custom-001",
            title="My Album",
            artist="My Artist",
            year=2025,
            genres=["Rock"],
            cover_art=cover_art_bytes,
            tracks=[Track(title="Song 1", duration=180, track_number=1)]
        )

        album_art = AlbumArt(cover_art_bytes)

        # Create card
        card = create_card_from_album(
            album,
            album_art,
            JCard4Panel,
            Theme(title_google_font="Orbitron", use_gradient=True)
        )
        ```
    """
    # Use default theme if none provided
    theme = theme or Theme()

    # Process theme: Register Google Fonts
    theme_updates = {}

    if theme.title_google_font:
        logger.info(f"Registering Google Font: {theme.title_google_font} (weight {theme.title_font_weight})")
        font_name = register_google_font(theme.title_google_font, theme.title_font_weight)
        if font_name:
            theme_updates["title_font"] = font_name
        else:
            theme_updates["title_font"] = f"{theme.font_family}-Bold"

    if theme.artist_google_font:
        logger.info(f"Registering Google Font: {theme.artist_google_font} (weight {theme.artist_font_weight})")
        font_name = register_google_font(theme.artist_google_font, theme.artist_font_weight)
        if font_name:
            theme_updates["artist_font"] = font_name
        else:
            theme_updates["artist_font"] = theme.font_family

    # Process theme: Extract gradient colors if enabled
    if theme.use_gradient:
        logger.info("Extracting color palette from album art...")
        extracted_palette = album_art.get_color_palette(max_colors=3)

        gradient_indices = theme.gradient_indices
        try:
            theme_updates["gradient_start"] = extracted_palette[gradient_indices[0]]
            theme_updates["gradient_end"] = extracted_palette[gradient_indices[1]]
            theme_updates["color_palette"] = extracted_palette
        except IndexError:
            logger.warning(
                f"Invalid gradient color indices {gradient_indices}, using first two colors."
            )
            theme_updates["gradient_start"] = extracted_palette[0]
            theme_updates["gradient_end"] = extracted_palette[1]
            theme_updates["color_palette"] = extracted_palette

    # Apply theme updates (if any)
    if theme_updates:
        theme = theme.model_copy(update=theme_updates)

    # Apply dolby logo setting
    if theme.dolby_logo:
        album.show_dolby_logo = True

    # Instantiate card
    card = card_class(album, theme, album_art, tape_length_minutes=theme.tape_length)

    logger.info(f"Created {card_class.__name__} for '{album.title}'")

    return card


def render_cards_to_pdf(
    cards: list[Card],
    output_path: str | Path,
    dpi: int = 600,
    page_size: str = "letter",
    include_crop_marks: bool = True,
) -> None:
    """
    Render multiple cards to a multi-page PDF.

    Cards are stacked vertically (2 per page) for efficient printing.

    Args:
        cards: List of Card objects to render.
        output_path: Path to output PDF file.
        dpi: DPI for image rendering (300-1200). Default: 600.
        page_size: Page size for printing. Default: "letter".
                  Options: "letter", "half", "a4", "a5", etc.
        include_crop_marks: Whether to include crop marks and fold guides. Default: True.

    Example:
        ```python
        from cardgen import Theme, create_card, render_cards_to_pdf, load_config
        from cardgen.design import JCard4Panel

        config = load_config()

        # Create multiple cards
        card1 = create_card("album/abc123", config, JCard4Panel)
        card2 = create_card("album/xyz789", config, JCard4Panel, Theme(use_gradient=True))

        # Render to PDF
        render_cards_to_pdf([card1, card2], "my_cards.pdf", dpi=720)
        ```
    """
    if not cards:
        raise ValueError("No cards provided to render")

    output_path = Path(output_path)

    logger.info(
        f"Rendering {len(cards)} card(s) to PDF at {dpi} DPI "
        f"on {page_size} page with {'crop marks' if include_crop_marks else 'no crop marks'}..."
    )

    renderer = PDFRenderer(
        dpi=dpi,
        include_crop_marks=include_crop_marks,
        page_size=page_size,
    )

    renderer.render_cards(cards, output_path)

    logger.info(f"PDF saved to: {output_path}")
