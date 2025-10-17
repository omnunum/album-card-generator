"""Print specifications and dimension utilities."""

from dataclasses import dataclass as _dataclass


@_dataclass(frozen=True)
class PageSize:
    """Page size specification."""

    width: float   # inches
    height: float  # inches
    label: str     # display label for CLI/help


# Registry of standard page sizes
PAGE_SIZES = {
    "letter": PageSize(8.5, 11.0, "Letter (8.5×11)"),
    "half": PageSize(8.5, 5.5, "Half Sheet (8.5×5.5)"),
    "a4": PageSize(8.27, 11.69, "A4 (210×297mm)"),
    "a5": PageSize(5.83, 8.27, "A5 (148×210mm)"),
}


def get_page_size(name: str) -> PageSize:
    """
    Get page size by name.

    Args:
        name: Page size name (e.g., "letter", "half", "a4").

    Returns:
        PageSize object. Defaults to letter if name not found.
    """
    return PAGE_SIZES.get(name.lower(), PAGE_SIZES["letter"])


# Standard cassette j-card dimensions (in inches)
JCARD_SPINE_WIDTH = 0.5
JCARD_BACK_WIDTH = 0.667  # Back panel (metadata section) - 2/3 inch
JCARD_HEIGHT = 4.0
JCARD_PANEL_WIDTH = 2.5  # Front and inside panels

# 4-panel j-card: Inside | Back | Spine | Front
# Total width: 2.5" + 0.667" + 0.5" + 2.5" = 6.167"
JCARD_4_PANEL_WIDTH = JCARD_PANEL_WIDTH + JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH
JCARD_4_PANEL_HEIGHT = JCARD_HEIGHT

# Print specifications
BLEED = 0.125  # 1/8 inch bleed on all sides
SAFE_MARGIN = 0.125  # 1/8 inch safety margin for text/logos

# Default page size (backward compatibility - for center_on_page default)
PAGE_WIDTH = 8.5
PAGE_HEIGHT = 11.0

# DPI settings
DPI_MIN = 300
DPI_RECOMMENDED = 600
DPI_MAX = 1200


@_dataclass
class Dimensions:
    """Dimensions for a specific element or area."""

    width: float  # inches
    height: float  # inches
    x: float = 0.0  # x position (inches)
    y: float = 0.0  # y position (inches)

    def to_points(self) -> tuple[float, float, float, float]:
        """
        Convert dimensions to points (72 points per inch).

        Returns:
            Tuple of (width, height, x, y) in points.
        """
        return (
            self.width * 72,
            self.height * 72,
            self.x * 72,
            self.y * 72,
        )

    def with_bleed(self) -> "Dimensions":
        """
        Return dimensions including bleed area.

        Returns:
            New Dimensions object with bleed added.
        """
        return Dimensions(
            width=self.width + (BLEED * 2),
            height=self.height + (BLEED * 2),
            x=self.x - BLEED,
            y=self.y - BLEED,
        )

    def with_safe_margin(self) -> "Dimensions":
        """
        Return dimensions excluding safe margin.

        Returns:
            New Dimensions object with safe margin subtracted.
        """
        return Dimensions(
            width=self.width - (SAFE_MARGIN * 2),
            height=self.height - (SAFE_MARGIN * 2),
            x=self.x + SAFE_MARGIN,
            y=self.y + SAFE_MARGIN,
        )


def get_jcard_4_panel_dimensions() -> Dimensions:
    """
    Get dimensions for standard 4-panel j-card.

    Returns:
        Dimensions object for 4-panel j-card.
    """
    return Dimensions(
        width=JCARD_4_PANEL_WIDTH,
        height=JCARD_4_PANEL_HEIGHT,
    )


def get_panel_dimensions() -> dict[str, Dimensions]:
    """
    Get dimensions for each panel in 4-panel j-card layout.

    Layout (left to right): Back | Spine | Front | Inside
    When folded, Back wraps around outside back, Front is outside front, Inside opens to the right.

    Returns:
        Dictionary mapping panel names to Dimensions.
    """
    # Layout: Back | Spine | Front | Inside
    # Back (1.0") | Spine (0.5") | Front (2.5") | Inside (2.5")
    return {
        "back": Dimensions(
            width=JCARD_BACK_WIDTH,
            height=JCARD_HEIGHT,
            x=0,
            y=0,
        ),
        "spine": Dimensions(
            width=JCARD_SPINE_WIDTH,
            height=JCARD_HEIGHT,
            x=JCARD_BACK_WIDTH,
            y=0,
        ),
        "front": Dimensions(
            width=JCARD_PANEL_WIDTH,
            height=JCARD_HEIGHT,
            x=JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH,
            y=0,
        ),
        "inside": Dimensions(
            width=JCARD_PANEL_WIDTH,
            height=JCARD_HEIGHT,
            x=JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH,
            y=0,
        ),
    }


def center_on_page(content_width: float, content_height: float, page_width: float = PAGE_WIDTH, page_height: float = PAGE_HEIGHT) -> tuple[float, float]:
    """
    Calculate position to center content on a page.

    Args:
        content_width: Width of content in inches.
        content_height: Height of content in inches.
        page_width: Width of page in inches (default: letter).
        page_height: Height of page in inches (default: letter).

    Returns:
        Tuple of (x, y) position in inches to center content.
    """
    x = (page_width - content_width) / 2
    y = (page_height - content_height) / 2
    return (x, y)


def inches_to_points(inches: float) -> float:
    """
    Convert inches to points (72 points per inch).

    Args:
        inches: Measurement in inches.

    Returns:
        Measurement in points.
    """
    return inches * 72


def points_to_inches(points: float) -> float:
    """
    Convert points to inches.

    Args:
        points: Measurement in points.

    Returns:
        Measurement in inches.
    """
    return points / 72
