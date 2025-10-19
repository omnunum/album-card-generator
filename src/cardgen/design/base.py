"""Base abstractions for card layouts and themes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cardgen.api.models import Album
from cardgen.types import CoverArtAlign, CoverArtMode, TrackTitleOverflow
from cardgen.utils.dimensions import Dimensions

if TYPE_CHECKING:
    from reportlab.pdfgen import canvas


@dataclass
class ColorScheme:
    """Color scheme for theme."""

    background: tuple[float, float, float]  # RGB 0-1
    text: tuple[float, float, float]  # RGB 0-1
    accent: tuple[float, float, float]  # RGB 0-1
    # Gradient support
    gradient_enabled: bool = False  # Whether to use gradient background
    gradient_start: tuple[float, float, float] | None = None  # RGB 0-1 for gradient start
    gradient_end: tuple[float, float, float] | None = None  # RGB 0-1 for gradient end


@dataclass
class FontConfig:
    """Font configuration for theme."""

    family: str
    monospace_family: str  # For fixed-width content (track numbers, durations)
    title_size: int
    artist_size: int
    track_size: int
    metadata_size: int


@dataclass
class RendererContext:
    """Context passed to section renderers."""

    canvas: "canvas.Canvas"  # type: ignore
    x: float  # X position in points
    y: float  # Y position in points
    width: float  # Width in points
    height: float  # Height in points
    font_config: "FontConfig"
    color_scheme: "ColorScheme"
    padding: float  # Padding in points
    dpi: int  # DPI for image rendering


class CardSection(ABC):
    """Base class for card sections."""

    def __init__(self, name: str, dimensions: Dimensions) -> None:
        """
        Initialize card section.

        Args:
            name: Section name (e.g., "front", "inside", "spine").
            dimensions: Section dimensions.
        """
        self.name = name
        self.dimensions = dimensions

    @abstractmethod
    def render(self, context: RendererContext) -> None:
        """
        Render this section to PDF canvas.

        Args:
            context: Rendering context with canvas, bounds, theme, etc.
        """
        pass


class Theme(ABC):
    """Abstract base class for card themes."""

    @abstractmethod
    def get_font_config(self) -> FontConfig:
        """
        Get font configuration for this theme.

        Returns:
            FontConfig object.
        """
        pass

    @abstractmethod
    def get_color_scheme(self) -> ColorScheme:
        """
        Get color scheme for this theme.

        Returns:
            ColorScheme object.
        """
        pass

    @abstractmethod
    def get_padding(self) -> float:
        """
        Get default padding in inches.

        Returns:
            Padding in inches.
        """
        pass

    @abstractmethod
    def get_track_title_overflow(self) -> TrackTitleOverflow:
        """
        Get track title overflow mode for tracklists.

        Returns:
            "truncate" or "wrap".
        """
        pass

    @abstractmethod
    def get_cover_art_mode(self) -> CoverArtMode:
        """
        Get cover art display mode.

        Returns:
            "square" or "fullscale".
        """
        pass

    @abstractmethod
    def get_cover_art_align(self) -> CoverArtAlign:
        """
        Get cover art horizontal alignment for fullscale mode.

        Returns:
            "center", "left", or "right".
        """
        pass

    @abstractmethod
    def get_min_track_title_char_spacing(self) -> float:
        """
        Get minimum character spacing for track titles.

        Returns:
            Minimum character spacing (negative = compressed).
        """
        pass


class Card(ABC):
    """Abstract base class for card layouts."""

    def __init__(self, album: Album, theme: Theme, tape_length_minutes: int = 90) -> None:
        """
        Initialize card with album data and theme.

        Args:
            album: Album data to display.
            theme: Theme for styling.
            tape_length_minutes: Length of cassette tape in minutes (default: 90 for C90).
        """
        self.album = album
        self.theme = theme
        self.tape_length_minutes = tape_length_minutes

    @abstractmethod
    def get_dimensions(self) -> Dimensions:
        """
        Get overall card dimensions.

        Returns:
            Dimensions object for entire card.
        """
        pass

    @abstractmethod
    def get_sections(self) -> list[CardSection]:
        """
        Get all sections that make up this card.

        Returns:
            List of CardSection objects.
        """
        pass

    @abstractmethod
    def get_fold_lines(self) -> list[float]:
        """
        Get x-coordinates of fold lines (in inches from left edge).

        Returns:
            List of x-coordinates for fold lines.
        """
        pass
