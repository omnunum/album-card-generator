"""Base abstractions for card layouts and themes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cardgen.api.models import Album
from cardgen.types import SizeStyle
from cardgen.utils.dimensions import Dimensions

from reportlab.pdfgen import canvas

if TYPE_CHECKING:
    from cardgen.config import Theme


@dataclass
class RendererContext:
    """Context passed to section renderers."""

    canvas: canvas.Canvas  # type: ignore
    x: float  # X position in points
    y: float  # Y position in points
    width: float  # Width in points
    height: float  # Height in points
    theme: "Theme"  # Theme with all visual settings
    padding: float  # Padding in points
    dpi: int  # DPI for image rendering


class CardSection(ABC):
    """Base class for card sections."""

    def __init__(self, name: str, dimensions: Dimensions, size_style: SizeStyle = "full") -> None:
        """
        Initialize card section.

        Args:
            name: Section name (e.g., "front", "inside", "spine").
            dimensions: Section dimensions.
            size_style: Size style - "full" or "compact" (default: "full").
        """
        self.name = name
        self.dimensions = dimensions
        self.size_style = size_style

    @abstractmethod
    def render(self, context: RendererContext) -> None:
        """
        Render this section to PDF canvas.

        Args:
            context: Rendering context with canvas, bounds, theme, etc.
        """
        pass


class Card(ABC):
    """Abstract base class for card layouts."""

    def __init__(self, album: Album, theme: "Theme", tape_length_minutes: int = 90) -> None:  # type: ignore
        """
        Initialize card with album data and theme.

        Args:
            album: Album data to display.
            theme: Theme configuration (Pydantic model from cardgen.config).
            tape_length_minutes: Length of cassette tape in minutes (default: 90 for C90).
        """
        self.album = album
        self.theme = theme  # This is cardgen.config.Theme (Pydantic model)
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
