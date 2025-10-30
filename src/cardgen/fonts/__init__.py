"""Font registration and management."""

import logging
from pathlib import Path
from typing import Optional

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from cardgen.fonts.google import get_google_font

logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).parent


def register_fonts() -> None:
    """
    Register custom fonts with ReportLab.

    Attempts to register Iosevka Regular and Bold. Falls back to Helvetica
    (PDF built-in) if font files are not found.

    Expected font files:
        - iosevka-regular.ttf
        - iosevka-bold.ttf

    Font files should be placed in the src/cardgen/fonts/ directory.
    """
    fonts_to_register = [
        ("Iosevka", "iosevka-regular.ttf"),
        ("Iosevka-Bold", "iosevka-bold.ttf"),
    ]

    for font_name, font_file in fonts_to_register:
        font_path = FONTS_DIR / font_file

        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                logger.info(f"Registered font: {font_name} from {font_file}")
            except Exception as e:
                logger.warning(
                    f"Failed to register font {font_name} from {font_file}: {e}. "
                    "Falling back to Helvetica."
                )
        else:
            logger.warning(
                f"Font file not found: {font_path}. "
                f"To use Iosevka, place {font_file} in {FONTS_DIR}. "
                "Using Helvetica fallback."
            )


def is_iosevka_available() -> bool:
    """
    Check if Iosevka fonts are registered and available.

    Returns:
        True if Iosevka fonts are available, False otherwise.
    """
    try:
        # Try to get the font - this will raise an exception if not registered
        pdfmetrics.getFont("Iosevka")
        pdfmetrics.getFont("Iosevka-Bold")
        return True
    except Exception:
        return False


def register_google_font(family: str, weight: int = 400) -> Optional[str]:
    """
    Download and register a Google Font with ReportLab.

    Args:
        family: Font family name (e.g., "Orbitron", "Roboto").
        weight: Font weight (e.g., 400 for regular, 700 for bold).

    Returns:
        Registered font name (e.g., "Orbitron-700"), or None if registration failed.
    """
    # Generate registered font name
    font_name = f"{family.replace(' ', '')}-{weight}"

    # Check if already registered
    try:
        pdfmetrics.getFont(font_name)
        logger.info(f"Google Font already registered: {font_name}")
        return font_name
    except Exception:
        pass  # Not registered yet

    # Download the font
    font_path = get_google_font(family, weight)
    if not font_path:
        logger.error(f"Failed to download Google Font: {family} (weight {weight})")
        return None

    # Register with ReportLab
    try:
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
        logger.info(f"Registered Google Font: {font_name}")
        return font_name
    except Exception as e:
        logger.error(f"Failed to register Google Font {font_name}: {e}")
        return None
