"""Metadata section implementation."""

from reportlab.lib.colors import Color

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions
from cardgen.utils.genres import get_leaf_genres
from cardgen.utils.text import Line, fit_text_block


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

    def _build_text_lines_for_column(
        self, context: RendererContext, text_lines: list[str]
    ) -> list[Line]:
        """
        Build Line objects for a single column.

        Args:
            context: Rendering context with font configuration.
            text_lines: List of text strings for this column.

        Returns:
            List of Line objects.
        """
        lines: list[Line] = []
        for text in text_lines:
            lines.append(Line(
                text=text,
                point_size=self.font_size,
                leading_ratio=0.25,  # 25% line spacing (same as tracklist)
                fixed_size=False,  # Allow size reduction
                font_family=context.theme.font_family
            ))
        return lines

    def _render_fitted_column(
        self,
        context: RendererContext,
        fitted_lines: list[Line],
        x_offset: float,
        padding: float,
        rotated_width: float
    ) -> None:
        """
        Render a single column of fitted text (in rotated coordinate system).

        Args:
            context: Rendering context.
            fitted_lines: Fitted Line objects from fit_text_block.
            x_offset: X position for the column start.
            padding: Padding value.
            rotated_width: Width in rotated coordinate system (original height).
        """
        c = context.canvas

        # Start from top of rotated space
        y_start = rotated_width - padding
        if fitted_lines:
            y_start -= fitted_lines[0].point_size

        text_y = y_start

        for fitted_line in fitted_lines:
            c.setFont(fitted_line.font_family, fitted_line.point_size)
            c.setFillColor(Color(*context.theme.effective_text_color))

            # Draw text with horizontal scaling if needed
            if fitted_line.horizontal_scale < 1.0:
                c.saveState()
                c.translate(x_offset, text_y)
                c.scale(fitted_line.horizontal_scale, 1.0)
                c.drawString(0, 0, fitted_line.text)
                c.restoreState()
            else:
                c.drawString(x_offset, text_y, fitted_line.text)

            # Move down for next line
            text_y -= fitted_line.point_size + (fitted_line.point_size * fitted_line.leading_ratio)

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
        left_text_lines = []
        if leaf_genres:
            # First genre gets "Genre: " prefix
            left_text_lines.append(f"Genre: {leaf_genres[0]}")
            # Subsequent genres are indented to align with first genre
            # limit to three additional genres
            for genre in leaf_genres[1:4]:
                left_text_lines.append(f"            {genre}")

        # Right column: Album metadata
        right_text_lines = []
        if self.album.year:
            right_text_lines.append(f"Year: {self.album.year}")
        if self.album.label:
            right_text_lines.append(f"Label: {self.album.label}")
        if self.album.composer:
            right_text_lines.append(f"Composer: {self.album.composer}")

        # After rotation, available height for text is context.width
        # Available width is context.height (split into two halves for columns)
        available_height = context.width - (2 * padding)
        column_width = (context.height / 2) - (2 * padding)

        # Save state and set up rotation
        c.saveState()

        # Translate to bottom-left of where rotated content should appear, then rotate
        c.translate(context.x + context.width, context.y)
        c.rotate(90)  # 90 degrees counterclockwise

        # Now we're in a rotated coordinate system
        # Process and render left column
        if left_text_lines:
            left_lines = self._build_text_lines_for_column(context, left_text_lines)
            fitted_left = fit_text_block(
                c, left_lines, context,
                max_width=column_width,
                max_height=available_height,
                min_horizontal_scale=0.7,
                split_max=1,
                min_point_size=5.0
            )
            self._render_fitted_column(context, fitted_left, padding, padding, context.width)

        # Process and render right column
        if right_text_lines:
            right_lines = self._build_text_lines_for_column(context, right_text_lines)
            fitted_right = fit_text_block(
                c, right_lines, context,
                max_width=column_width,
                max_height=available_height,
                min_horizontal_scale=0.7,
                split_max=1,
                min_point_size=5.0
            )
            x_right = context.height / 2 + padding
            self._render_fitted_column(context, fitted_right, x_right, padding, context.width)

        c.restoreState()
