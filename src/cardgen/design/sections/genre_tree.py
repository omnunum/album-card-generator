"""Genre tree section implementation."""

import re

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions, inches_to_points
from cardgen.utils.genres import build_genre_tree
from cardgen.utils.text import Line, fit_text_block, TextBounds, render_fitted_text_with_prefix_suffix


class GenreTreeSection(CardSection):
    """Section displaying genre hierarchy tree."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album: Album,
        font_size: float = 7.0,
        padding_override: float | None = None,
        leading_ratio: float = 0.53,
    ) -> None:
        """
        Initialize genre tree section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album: Album object with genres.
            font_size: Font size in points (default: 7.0).
            padding_override: Custom padding in inches. If None, uses theme default.
            leading_ratio: Leading ratio for text (default: 0.53).
                          Updated from 0.4 to account for canonical formula using adjusted_point_size.
        """
        super().__init__(name, dimensions)
        self.album = album
        self.font_size = font_size
        self.padding_override = padding_override
        self.leading_ratio = leading_ratio

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
            leading_ratio=self.leading_ratio,
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
                    leading_ratio=self.leading_ratio,
                    fixed_size=False,  # Don't reduce or wrap ASCII art
                    font_family=context.theme.font_family,
                    prefix=prefix,  # Tree chars stay monospace, won't compress
                    prefix_horizontal_scale=0.7
                ))
            else:
                # Fallback: treat entire line as text
                lines.append(Line(
                    text=genre_line,
                    point_size=self.font_size,
                    leading_ratio=self.leading_ratio,
                    fixed_size=False,
                    font_family=context.theme.font_family
                ))

        return lines

    def render(self, context: RendererContext) -> None:
        """Render genre tree using centralized rendering."""
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

        # Create TextBounds for fitting and rendering (using relative coordinates)
        bounds = TextBounds.from_relative_context(context, padding)

        # Build Line objects
        lines = self._build_text_lines(context)

        # Fit all text within constraints
        # Uses canonical formula (glyph_height_adjusted=True by default)
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=bounds.width,
            max_height=bounds.height,
            min_horizontal_scale=0.6,
            split_max=1,
            min_point_size=5.0
        )

        # Render using centralized canonical renderer with prefix/suffix support
        render_fitted_text_with_prefix_suffix(
            fitted_lines,
            c,
            bounds,
            context,
            alignment="left"
        )

        c.restoreState()
