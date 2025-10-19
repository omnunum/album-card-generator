"""Metadata section implementation."""

from reportlab.lib.colors import Color

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions
from cardgen.utils.genres import get_leaf_genres


class MetadataSection(CardSection):
    """Metadata section with horizontal multi-line text in two columns."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album: Album,
        font_size: float = 5.0,
        padding_override: float | None = None,
    ) -> None:
        """
        Initialize metadata section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album: Album object with genres and metadata.
            font_size: Font size in points (default: 5.0).
            padding_override: Custom padding in inches. If None, uses theme default.
        """
        super().__init__(name, dimensions)
        self.album = album
        self.font_size = font_size
        self.padding_override = padding_override

    def render(self, context: RendererContext) -> None:
        """Render metadata content as two columns of vertical text (rotated 90 degrees)."""
        c = context.canvas

        # Use custom padding if provided, otherwise use theme default
        if self.padding_override is not None:
            padding = self.padding_override * 72  # Convert inches to points
        else:
            padding = context.padding

        # Process album data into left and right columns
        # Left column: Leaf genres
        leaf_genres = get_leaf_genres(self.album.genres)
        left_lines = []
        if leaf_genres:
            # First genre gets "Genre: " prefix
            left_lines.append(f"Genre: {leaf_genres[0]}")
            # Subsequent genres are indented to align with first genre
            for genre in leaf_genres[1:]:
                left_lines.append(f"            {genre}")

        # Right column: Album metadata
        right_lines = []
        if self.album.year:
            right_lines.append(f"Year: {self.album.year}")
        if self.album.label:
            right_lines.append(f"Label: {self.album.label}")
        right_lines.append(f"Duration: {self.album.format_total_duration()}")
        right_lines.append(f"Tracks: {len(self.album.tracks)}")

        # Set up drawing
        c.setFillColor(Color(*context.color_scheme.text))
        c.setFont(context.font_config.family, self.font_size)

        line_height = self.font_size * 1.2  # 20% line spacing

        # Save state and set up rotation
        c.saveState()

        # Translate to bottom-left of where rotated content should appear, then rotate
        c.translate(context.x + context.width, context.y)
        c.rotate(90)  # 90 degrees counterclockwise

        # Now we're in a simple (0,0) coordinate system
        # Available space is (context.height × context.width) after rotation

        # Draw left column (genres) - first half
        x_left = padding
        y_start = context.width - padding - self.font_size

        for i, line in enumerate(left_lines):
            y = y_start - (i * line_height)
            if y < padding:  # Check bottom boundary
                break
            c.drawString(x_left, y, line)

        # Draw right column (metadata) - second half
        x_right = context.height / 2 + padding
        y_start = context.width - padding - self.font_size

        for i, line in enumerate(right_lines):
            y = y_start - (i * line_height)
            if y < padding:  # Check bottom boundary
                break
            c.drawString(x_right, y, line)

        c.restoreState()
