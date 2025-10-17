"""Font registration and management."""

import logging
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
