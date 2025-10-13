"""Configuration loading and validation."""

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class NavidromeConfig(BaseModel):
    """Navidrome server configuration."""

    url: str
    username: str
    password: str


class OutputTemplates(BaseModel):
    """Named output template patterns."""

    default: str = "{artist} - {album}.pdf"
    dated: str = "{artist} - {album} ({year}).pdf"
    simple: str = "{album}.pdf"


class OutputConfig(BaseModel):
    """Output configuration."""

    default_card_type: str = "jcard_4panel"
    default_theme: str = "default"
    default_page_size: str = "letter"
    dpi: int = Field(default=600, ge=300, le=1200)
    include_crop_marks: bool = True
    templates: OutputTemplates = Field(default_factory=OutputTemplates)


class ThemeColorScheme(BaseModel):
    """Theme color configuration."""

    background_color: list[float] = [1.0, 1.0, 1.0]
    text_color: list[float] = [0.0, 0.0, 0.0]
    accent_color: list[float] = [0.2, 0.2, 0.2]


class DefaultThemeConfig(BaseModel):
    """Default theme configuration."""

    font_family: str = "Helvetica"
    title_font_size: int = 14
    artist_font_size: int = 12
    track_font_size: int = 10
    metadata_font_size: int = 8
    background_color: list[float] = [1.0, 1.0, 1.0]
    text_color: list[float] = [0.0, 0.0, 0.0]
    accent_color: list[float] = [0.2, 0.2, 0.2]


class ThemesConfig(BaseModel):
    """All theme configurations."""

    default: DefaultThemeConfig = Field(default_factory=DefaultThemeConfig)


class Config(BaseModel):
    """Root configuration."""

    navidrome: NavidromeConfig
    output: OutputConfig = Field(default_factory=OutputConfig)
    themes: ThemesConfig = Field(default_factory=ThemesConfig)


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
