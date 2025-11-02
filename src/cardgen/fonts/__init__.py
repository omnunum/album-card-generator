"""Font registration and management."""

import logging
from pathlib import Path
from typing import Optional

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from cardgen.fonts.google import get_google_font

logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).parent

# Font path registry: maps registered font names to their file paths
# This is needed for text measurement using HarfBuzz/FreeType
_FONT_PATHS: dict[str, Path] = {}


def _normalize_font_name(name: str) -> str:
    """
    Normalize a font name to TitleCase convention.

    Converts hyphen-separated parts to Title Case to match PostScript naming.

    Examples:
        "iosevka-regular" → "Iosevka-Regular"
        "helvetica-bold" → "Helvetica-Bold"
        "stop" → "Stop"
        "roboto-mono" → "Roboto-Mono"

    Args:
        name: Font name to normalize (can be any case)

    Returns:
        TitleCase font name
    """
    # Split by hyphens, title-case each part, rejoin
    parts = name.split('-')
    return '-'.join(part.title() for part in parts)


def register_fonts() -> None:
    """
    Register custom fonts with ReportLab.

    Auto-discovers and registers all TTF font files in the fonts directory.
    Each font is registered with a TitleCase name based on its filename (without extension).

    Examples:
        - iosevka-regular.ttf → registered as "Iosevka-Regular"
        - Iosevka-Bold.ttf → registered as "Iosevka-Bold"
        - my-custom-font.ttf → registered as "My-Custom-Font"
        - stop.ttf → registered as "Stop"

    Font files should be placed in the src/cardgen/fonts/ directory.
    Falls back to Helvetica (PDF built-in) if no fonts are found or registration fails.
    """

    # Find all TTF files in fonts directory
    ttf_files = sorted(FONTS_DIR.glob("*.ttf"))

    if not ttf_files:
        logger.warning(
            f"No TTF font files found in {FONTS_DIR}. "
            "Using built-in fonts (Helvetica, Courier). "
            "Place .ttf files in the fonts directory to use custom fonts."
        )

    # Register each font with TitleCase name
    registered_count = 0
    for font_path in ttf_files:
        # Normalize filename to TitleCase
        font_name = _normalize_font_name(font_path.stem)

        try:
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            _FONT_PATHS[font_name] = font_path
            logger.info(f"Registered font: {font_name} from {font_path.name}")
            registered_count += 1
        except Exception as e:
            logger.warning(
                f"Failed to register font {font_name} from {font_path.name}: {e}. "
                "Skipping this font."
            )

    if registered_count == 0 and not ttf_files:
        logger.info("No custom fonts registered. Using built-in PDF fonts.")
    elif registered_count > 0:
        logger.info(f"Successfully registered {registered_count} custom font(s).")


def resolve_font(font_spec: str, fallback: str = "Helvetica") -> str:
    """
    Resolve a font specification to a registered font name (case-insensitive).

    All font names are normalized to TitleCase for consistency with PostScript naming.

    Resolution priority:
    1. Check if already registered (TTF fonts or PDF built-ins)
    2. Try Google Fonts (auto-download and cache)
    3. Fall back to specified fallback font

    Args:
        font_spec: Font specification, case-insensitive. Can be:
                  - Simple name: "myfont" or "MyFont"
                  - With weight: "myfont:700" or "MyFont:700"
        fallback: Fallback font name (default: "Helvetica")

    Returns:
        TitleCase font name

    Examples:
        >>> resolve_font("helvetica")
        "Helvetica"  # Normalized to TitleCase

        >>> resolve_font("orbitron:700")
        "Orbitron-700"  # Downloaded from Google Fonts if not local

        >>> resolve_font("NonExistentFont")
        "Helvetica"  # Falls back to Helvetica
    """
    # Parse family:weight format
    if ":" in font_spec:
        family, weight_str = font_spec.split(":", 1)
        family = family.strip()
        weight_str = weight_str.strip()

        try:
            weight = int(weight_str)
            # Normalize to TitleCase with weight
            font_name = f"{_normalize_font_name(family)}-{weight}"
        except ValueError:
            logger.warning(f"Invalid font weight '{weight_str}' in '{font_spec}', using as-is")
            # Normalize the whole thing to TitleCase
            font_name = _normalize_font_name(font_spec.replace(":", "-"))
            weight = None
    else:
        # Normalize to TitleCase
        font_name = _normalize_font_name(font_spec.strip())
        family = font_spec.strip()
        weight = None

    # 1. Check if already registered (works for both built-ins and TTF fonts)
    try:
        pdfmetrics.getFont(font_name)
        logger.debug(f"Font '{font_name}' found in registry")
        return font_name
    except Exception:
        pass

    # 2. Try Google Fonts (if weight specified)
    if weight is not None:
        logger.info(f"Font '{font_name}' not found locally, trying Google Fonts...")
        result = register_google_font(family, weight)
        if result:
            return result
        logger.warning(f"Could not download '{font_name}' from Google Fonts")

    # 3. Fall back
    fallback_normalized = _normalize_font_name(fallback)
    logger.info(f"Using fallback font '{fallback_normalized}' for '{font_spec}'")
    return fallback_normalized


def is_iosevka_available() -> bool:
    """
    Check if Iosevka fonts are registered and available.

    Returns:
        True if Iosevka fonts are available, False otherwise.
    """
    try:
        # Try to get the font - this will raise an exception if not registered
        # Check for TitleCase names
        pdfmetrics.getFont("Iosevka-Regular")
        pdfmetrics.getFont("Iosevka-Bold")
        return True
    except Exception:
        return False


def register_google_font(family: str, weight: int = 400) -> Optional[str]:
    """
    Download and register a Google Font with ReportLab.

    Args:
        family: Font family name (e.g., "Orbitron", "Roboto") - case-insensitive.
        weight: Font weight (e.g., 400 for regular, 700 for bold).

    Returns:
        Registered font name in TitleCase (e.g., "Orbitron-700"), or None if registration failed.
    """
    # Normalize family name to TitleCase and generate font name
    family_normalized = _normalize_font_name(family.replace(' ', ''))
    font_name = f"{family_normalized}-{weight}"

    # Check if already registered
    try:
        pdfmetrics.getFont(font_name)
        logger.info(f"Google Font already registered: {font_name}")
        return font_name
    except Exception:
        pass  # Not registered yet

    # Download the font (Google Fonts API handles case-insensitive lookup)
    # Note: Cache filenames remain lowercase for filesystem compatibility
    font_path = get_google_font(family, weight)
    if not font_path:
        logger.error(f"Failed to download Google Font: {family} (weight {weight})")
        return None

    # Register with ReportLab (with TitleCase name)
    try:
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
        _FONT_PATHS[font_name] = font_path
        logger.info(f"Registered Google Font: {font_name}")
        return font_name
    except Exception as e:
        logger.error(f"Failed to register Google Font {font_name}: {e}")
        return None


def get_font_path(font_name: str) -> Optional[Path]:
    """
    Get the file path for a registered font.

    Args:
        font_name: Registered font name (e.g., "Iosevka", "Orbitron-700").

    Returns:
        Path to the font file, or None if font path is not tracked.
        Note: PDF built-in fonts (Helvetica, Courier, etc.) won't have paths.
    """
    return _FONT_PATHS.get(font_name)
