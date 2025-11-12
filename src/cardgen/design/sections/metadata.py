"""Metadata section implementation."""
import re

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions, inches_to_points
from cardgen.utils.genres import get_leaf_genres
from cardgen.utils.text import Line, fit_text_block, TextBounds, render_fitted_text_with_prefix_suffix


class MetadataSection(CardSection):
    """Metadata section with horizontal multi-line text in two columns."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album: Album,
        font_size: float = 5.0,
        padding: float = 1/16,
        leading_ratio: float = 0.33,
    ) -> None:
        """
        Initialize metadata section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album: Album object with genres and metadata.
            font_size: Font size in points (default: 5.0).
            padding: Padding in inches (default: 1/16).
            leading_ratio: Leading ratio for text (default: 0.33).
                          Updated from 0.25 to account for canonical formula using adjusted_point_size.
        """
        super().__init__(name, dimensions)
        self.album = album
        self.font_size = font_size
        self.padding = padding
        self.leading_ratio = leading_ratio

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
            match = re.match(r'^(\s+)?(.+)$', text)
            if match:
                prefix = match.group(1) or ""  # Tree characters (monospace)
                genre_name = match.group(2)    # Genre name (proportional font)

                lines.append(Line(
                    prefix=prefix,
                    text=genre_name,
                    point_size=self.font_size,
                    leading_ratio=self.leading_ratio,
                    fixed_size=False,  # Allow size reduction
                    font_family=context.theme.font_family
                ))
            else:
                lines.append(Line(
                    text=text,
                    point_size=self.font_size,
                    leading_ratio=self.leading_ratio,
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
        rotated_width: float,
        column_width: float
    ) -> None:
        """
        Render a single column of fitted text (in rotated coordinate system).

        Args:
            context: Rendering context.
            fitted_lines: Fitted Line objects from fit_text_block.
            x_offset: X position for the column start.
            padding: Padding value.
            rotated_width: Width in rotated coordinate system (original height).
            column_width: Width available for the column text.
        """
        # Create TextBounds for this column (in rotated coordinate system)
        # Note: We're already in a rotated coordinate system, so coordinates are relative
        bounds = TextBounds(
            x=x_offset,
            y=padding,
            width=column_width,
            height=rotated_width - (padding * 2)
        )

        # Render using centralized canonical renderer
        render_fitted_text_with_prefix_suffix(
            fitted_lines,
            context.canvas,
            bounds,
            context,
            alignment="left"
        )

    def render(self, context: RendererContext) -> None:
        """Render metadata content as two columns of vertical text (rotated 90 degrees)."""
        c = context.canvas

        # Convert padding from inches to points
        padding = inches_to_points(self.padding)

        # Process album data into left and right columns
        # Left column: Leaf genres
        leaf_genres = get_leaf_genres(self.album.genres)
        left_text_lines : list[str] = []
        if leaf_genres:
            # First genre gets "Genre: " prefix
            left_text_lines.append(f"Genre: {leaf_genres[0]}")
            # Subsequent genres are indented to align with first genre
            # limit to three additional genres
            for genre in leaf_genres[1:3]:
                left_text_lines.append(f"  {genre}")

        # Right column: Album metadata
        right_text_lines : list[str] = []
        if self.album.year:
            right_text_lines.append(f"Year: {self.album.year}")
        if self.album.label:
            right_text_lines.append(f"Label: {self.album.label}")
        if self.album.composer:
            right_text_lines.append(f"Composer: {self.album.composer}")

        # After rotation, available height for text is context.width
        # Available width is context.height (split into two halves for columns)
        # Padding is applied to the entire section edges, with a gap between columns
        available_height = context.width - (2 * padding)
        column_gap = padding  # Gap between the two columns
        column_width = (context.height - (2 * padding) - column_gap) / 2

        # Save state and set up rotation
        c.saveState()

        # Translate to bottom-right corner, then rotate 90 degrees counterclockwise
        c.translate(context.x + context.width, context.y)
        c.rotate(90)

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
                min_point_size=4.0
            )
            self._render_fitted_column(context, fitted_left, padding, padding, context.width, column_width)

        # Process and render right column
        if right_text_lines:
            right_lines = self._build_text_lines_for_column(context, right_text_lines)
            fitted_right = fit_text_block(
                c, right_lines, context,
                max_width=column_width,
                max_height=available_height,
                min_horizontal_scale=0.7,
                split_max=1,
                min_point_size=4.0
            )
            # Right column starts after left column plus the gap between columns
            x_right = padding + column_width + column_gap
            self._render_fitted_column(context, fitted_right, x_right, padding, context.width, column_width)

        c.restoreState()
