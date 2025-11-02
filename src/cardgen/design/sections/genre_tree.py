"""Genre tree section implementation."""

import re
from reportlab.lib.colors import Color

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions, inches_to_points
from cardgen.utils.genres import build_genre_tree
from cardgen.utils.text import Line, fit_text_block


class GenreTreeSection(CardSection):
    """Section displaying genre hierarchy tree."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album: Album,
        font_size: float = 7.0,
        padding_override: float | None = None,
    ) -> None:
        """
        Initialize genre tree section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album: Album object with genres.
            font_size: Font size in points (default: 7.0).
            padding_override: Custom padding in inches. If None, uses theme default.
        """
        super().__init__(name, dimensions)
        self.album = album
        self.font_size = font_size
        self.padding_override = padding_override

    def _build_text_lines(self, context: RendererContext) -> list[Line]:
        """
        Build Line objects for genre tree.

        Args:
            context: Rendering context with font configuration.

        Returns:
            List of Line objects representing genre tree text.
        """
        lines: list[Line] = []

        # Build genre tree
        genre_tree = build_genre_tree(self.album.genres) if self.album.genres else ""

        # Add genre tree lines
        if not genre_tree:
            return lines
        # Header line
        lines.append(Line(
            text="Genre Tree:",
            point_size=self.font_size,
            leading_ratio=0.4,  # 40% line spacing
            fixed_size=True,  # Don't reduce header
            font_family=f"{context.theme.font_family}-Bold"
        ))

        # Genre tree lines (ASCII art - fixed size)
        # Parse tree structure to separate tree characters from genre names
        genre_lines = genre_tree.split("\n")
        for genre_line in genre_lines:
            # Match tree prefix (optional tree chars like "│ ", "├─", "└─") and genre name
            # Pattern: optional tree characters followed by the genre name
            match = re.match(r'^([│├└─ ]+)?(.+)$', genre_line)
            if match:
                prefix = match.group(1) or ""  # Tree characters (monospace)
                genre_name = match.group(2)    # Genre name (proportional font)

                lines.append(Line(
                    text=genre_name,
                    point_size=self.font_size,
                    leading_ratio=0.4,
                    fixed_size=False,  # Don't reduce or wrap ASCII art
                    font_family=context.theme.font_family,
                    prefix=prefix  # Tree chars stay monospace, won't compress
                ))
            else:
                # Fallback: treat entire line as text
                lines.append(Line(
                    text=genre_line,
                    point_size=self.font_size,
                    leading_ratio=0.4,
                    fixed_size=False,
                    font_family=context.theme.font_family
                ))

        return lines

    def _render_fitted_lines(
        self,
        context: RendererContext,
        fitted_lines: list[Line],
        start_y: float,
        padding: float
    ) -> None:
        """
        Render fitted text lines for genre tree.

        Args:
            context: Rendering context.
            fitted_lines: Fitted Line objects from fit_text_block.
            start_y: Starting y position (top of text area, relative to section origin).
            padding: Horizontal padding.
        """
        c = context.canvas
        text_y = start_y

        for fitted_line in fitted_lines:
            # Skip empty lines (spacing)
            if not fitted_line.text:
                text_y -= fitted_line.point_size + (fitted_line.point_size * fitted_line.leading_ratio)
                continue

            c.setFillColor(Color(*context.theme.effective_text_color))

            # Get fonts for prefix/suffix
            prefix_font = fitted_line.prefix_font or context.theme.monospace_family
            suffix_font = fitted_line.suffix_font or context.theme.monospace_family

            # Calculate prefix width
            prefix_width = c.stringWidth(fitted_line.prefix, prefix_font, fitted_line.point_size) if fitted_line.prefix else 0

            # Draw prefix (tree characters - monospace, never compressed)
            if fitted_line.prefix:
                c.setFont(prefix_font, fitted_line.point_size)
                c.drawString(padding, text_y, fitted_line.prefix)

            # Draw text (genre name - proportional font, can be compressed)
            c.setFont(fitted_line.font_family, fitted_line.point_size)
            if fitted_line.horizontal_scale < 1.0:
                c.saveState()
                c.translate(padding + prefix_width, text_y)
                c.scale(fitted_line.horizontal_scale, 1.0)
                c.drawString(0, 0, fitted_line.text)
                c.restoreState()
            else:
                c.drawString(padding + prefix_width, text_y, fitted_line.text)

            # Draw suffix if present (though genre tree typically doesn't have suffixes)
            if fitted_line.suffix:
                suffix_width = c.stringWidth(fitted_line.suffix, suffix_font, fitted_line.point_size)
                available_width = context.width - (padding * 2)
                suffix_x = padding + available_width - suffix_width
                c.setFont(suffix_font, fitted_line.point_size)
                c.drawString(suffix_x, text_y, fitted_line.suffix)

            # Move down for next line
            text_y -= fitted_line.point_size + (fitted_line.point_size * fitted_line.leading_ratio)

    def render(self, context: RendererContext) -> None:
        """Render genre tree using fit_text_block."""
        c = context.canvas

        # Establish local coordinate system
        c.saveState()
        c.translate(context.x, context.y)

        # Use custom padding if provided, otherwise use larger padding for genre panel
        if self.padding_override is not None:
            padding = inches_to_points(self.padding_override)
        else:
            # Use larger padding for genre panel (0.15" = 10.8 points instead of default ~7.2 points)
            padding = inches_to_points(0.15)

        # Calculate available space
        available_height = context.height - (padding * 2)
        available_width = context.width - (padding * 2)

        # Build Line objects
        lines = self._build_text_lines(context)

        # Fit all text within constraints
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=available_width,
            max_height=available_height,
            min_horizontal_scale=0.6,
            split_max=1,
            min_point_size=5.0
        )

        # Render fitted lines (using relative coordinates now)
        start_y = context.height - padding - fitted_lines[0].point_size
        self._render_fitted_lines(context, fitted_lines, start_y, padding)

        c.restoreState()
