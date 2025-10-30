"""Configuration loading and validation."""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from cardgen.types import CoverArtAlign, CoverArtMode, TrackTitleOverflow


class NavidromeConfig(BaseModel):
    """Navidrome server configuration."""

    url: str
    username: str
    password: str


class Theme(BaseModel):
    """
    Complete theme configuration with all visual settings.

    All parameters have sensible defaults. Override only what you need using
    Pydantic's model_copy():

        base = Theme(title_google_font="Orbitron")
        variant = base.model_copy(update={"use_gradient": True})
    """

    # ========================================================================
    # Fonts
    # ========================================================================
    font_family: str = "Helvetica"
    """Base font family for variable-width text (titles, artist, tracks)."""

    monospace_family: str = "Iosevka"
    """Font for fixed-width content (track numbers, durations). Falls back to Courier if unavailable."""

    title_google_font: str | None = None
    """Google Font for album title (e.g., "Orbitron"). Auto-downloaded and cached."""

    title_font_weight: int = 700
    """Font weight for title (100-900). Default: 700 (Bold)."""

    artist_google_font: str | None = None
    """Google Font for artist name (e.g., "Roboto"). Auto-downloaded and cached."""

    artist_font_weight: int = 400
    """Font weight for artist (100-900). Default: 400 (Regular)."""

    title_size: int = 14
    """Font size for album title in points."""

    artist_size: int = 12
    """Font size for artist name in points."""

    subtitle_size: int = 12
    """Font size for side headers (Side A/B) and minimap in points."""

    track_size: int = 10
    """Font size for track titles in points."""

    metadata_size: int = 8
    """Font size for metadata text in points."""

    # ========================================================================
    # Computed Fonts (filled by factory after processing)
    # ========================================================================
    title_font: str = "Helvetica-Bold"
    """Resolved font name for title (e.g., "Orbitron-900" after Google Font registration)."""

    artist_font: str = "Helvetica"
    """Resolved font name for artist (e.g., "Roboto-400" after Google Font registration)."""

    # ========================================================================
    # Colors
    # ========================================================================
    background: tuple[float, float, float] = (1.0, 1.0, 1.0)
    """Background color as RGB in 0-1 range. Default: white."""

    text: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Text color as RGB in 0-1 range. Default: black."""

    accent: tuple[float, float, float] = (0.2, 0.2, 0.2)
    """Accent color as RGB in 0-1 range. Default: dark gray."""

    # ========================================================================
    # Gradient
    # ========================================================================
    use_gradient: bool = False
    """Extract gradient background colors from album art."""

    gradient_text: tuple[float, float, float] = (1.0, 1.0, 1.0)
    """Text color for gradient mode as RGB in 0-1 range. Default: white."""

    gradient_accent: tuple[float, float, float] = (0.8, 0.8, 0.8)
    """Accent color for gradient mode as RGB in 0-1 range. Default: light gray."""

    gradient_indices: tuple[int, int] = (0, 1)
    """Which colors from extracted palette to use for gradient (start_index, end_index)."""

    # ========================================================================
    # Computed Gradient Colors (filled by factory after color extraction)
    # ========================================================================
    gradient_start: tuple[float, float, float] | None = None
    """Starting color for gradient (extracted from album art)."""

    gradient_end: tuple[float, float, float] | None = None
    """Ending color for gradient (extracted from album art)."""

    color_palette: list[tuple[float, float, float]] | None = None
    """Full color palette extracted from album art (sorted by frequency)."""

    # ========================================================================
    # Cover Art
    # ========================================================================
    cover_art_mode: CoverArtMode = "square"
    """Cover art display mode: "square" (centered) or "fullscale" (full height with crop)."""

    cover_art_align: CoverArtAlign = "center"
    """Horizontal alignment for fullscale mode: "center", "left", or "right"."""

    # ========================================================================
    # Track Formatting
    # ========================================================================
    track_overflow: TrackTitleOverflow = "truncate"
    """Track title overflow handling: "truncate" (ellipsis) or "wrap" (line break)."""

    min_char_spacing: float = -1.0
    """Minimum character spacing for track titles (negative = compressed). -1.0 = aggressive."""

    # ========================================================================
    # Card Settings
    # ========================================================================
    padding: float = 0.125
    """Default padding in inches."""

    tape_length: int = 90
    """Cassette tape length in minutes (for side balancing). Default: 90 (C90)."""

    dolby_logo: bool = False
    """Show Dolby NR logo on the spine."""

    # ========================================================================
    # Computed Properties
    # ========================================================================

    @property
    def effective_monospace_family(self) -> str:
        """
        Get monospace font family with Iosevka fallback.

        Returns "Courier" if Iosevka is specified but not available.
        """
        if self.monospace_family == "Iosevka":
            from cardgen.fonts import is_iosevka_available
            if not is_iosevka_available():
                return "Courier"
        return self.monospace_family

    @property
    def effective_text_color(self) -> tuple[float, float, float]:
        """
        Get text color based on gradient mode.

        Returns gradient_text if use_gradient is True, otherwise text.
        """
        return self.gradient_text if self.use_gradient else self.text

    @property
    def effective_accent_color(self) -> tuple[float, float, float]:
        """
        Get accent color based on gradient mode.

        Returns gradient_accent if use_gradient is True, otherwise accent.
        """
        return self.gradient_accent if self.use_gradient else self.accent


class Config(BaseModel):
    """Root configuration (minimal - just Navidrome credentials)."""

    navidrome: NavidromeConfig


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from TOML file.

    Args:
        config_path: Path to config file. If None, looks for config.toml in current directory.

    Returns:
        Validated Config object.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config is invalid.
    """
    if config_path is None:
        config_path = Path.cwd() / "config.toml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            "Copy config.toml.example to config.toml and add your credentials."
        )

    with open(config_path, "rb") as f:
        config_dict = tomllib.load(f)

    return Config(**config_dict)


def format_output_name(
    template: str, artist: str, album: str, year: int | None = None
) -> str:
    """
    Format output filename using template.

    Args:
        template: Template string with placeholders.
        artist: Artist name.
        album: Album name.
        year: Optional year.

    Returns:
        Formatted filename.
    """
    # Sanitize values for filenames
    safe_artist = sanitize_filename(artist)
    safe_album = sanitize_filename(album)
    safe_year = str(year) if year else "Unknown"

    return template.format(
        artist=safe_artist,
        album=safe_album,
        year=safe_year,
        date=safe_year,  # alias
    )


def sanitize_filename(name: str) -> str:
    """
    Sanitize string for use in filename.

    Args:
        name: String to sanitize.

    Returns:
        Sanitized string safe for filenames.
    """
    # Replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")

    # Remove leading/trailing whitespace and dots
    name = name.strip(". ")

    return name
