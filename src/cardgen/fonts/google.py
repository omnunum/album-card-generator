"""Google Fonts downloader and manager."""

import logging
import re
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Cache directory for downloaded Google Fonts
CACHE_DIR = Path.home() / ".cache" / "album-card-generator" / "fonts"


def get_google_font(family: str, weight: int = 400) -> Optional[Path]:
    """
    Download a Google Font and return the path to the cached TTF file.

    Args:
        family: Font family name (e.g., "Orbitron", "Roboto").
        weight: Font weight (e.g., 400 for regular, 700 for bold).

    Returns:
        Path to the cached TTF file, or None if download failed.
    """
    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate cache filename
    cache_filename = f"{family.replace(' ', '')}-{weight}.ttf"
    cache_path = CACHE_DIR / cache_filename

    # Return cached file if it exists
    if cache_path.exists():
        logger.info(f"Using cached Google Font: {cache_filename}")
        return cache_path

    # Construct Google Fonts CSS API v1 URL
    # Format: https://fonts.googleapis.com/css?family=Orbitron:400&display=swap
    font_url = f"https://fonts.googleapis.com/css?family={family.replace(' ', '+')}:{weight}&display=swap"

    try:
        logger.info(f"Downloading Google Font: {family} (weight {weight})")

        # Fetch CSS - v1 API typically returns TTF URLs
        css_response = requests.get(font_url, timeout=10)
        css_response.raise_for_status()

        # Parse CSS to extract font file URL
        font_file_url = _extract_font_url_from_css(css_response.text)
        if not font_file_url:
            logger.error(f"Failed to extract font URL from CSS for {family}")
            return None

        # Download the font file
        font_response = requests.get(font_file_url, timeout=30)
        font_response.raise_for_status()

        # Save to cache
        cache_path.write_bytes(font_response.content)
        logger.info(f"Downloaded and cached Google Font: {cache_filename}")

        return cache_path

    except requests.RequestException as e:
        logger.error(f"Failed to download Google Font {family} (weight {weight}): {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading Google Font {family}: {e}")
        return None


def _extract_font_url_from_css(css_content: str) -> Optional[str]:
    """
    Extract the font file URL from Google Fonts CSS.

    The CSS contains @font-face rules with src: url(...) format.

    Args:
        css_content: CSS content from Google Fonts API.

    Returns:
        URL to the font file (TTF), or None if not found.
    """
    # Look for url() in src property
    # Google Fonts CSS v1 typically provides TTF URLs with format('truetype')
    url_pattern = r'src:\s*url\((https://[^)]+\.ttf)\)'

    match = re.search(url_pattern, css_content)
    if match:
        return match.group(1)

    # Fallback: try to find any TTF URL
    ttf_pattern = r'(https://[^\s\'"]+\.ttf)'
    match = re.search(ttf_pattern, css_content)
    if match:
        return match.group(1)

    return None
