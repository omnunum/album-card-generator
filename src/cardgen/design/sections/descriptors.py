"""Descriptors section implementation."""

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions, inches_to_points
from cardgen.utils.text import Line, fit_text_block, TextBounds, render_fitted_text


class DescriptorsSection(CardSection):
    """Section displaying RYM descriptors."""

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
        Initialize descriptors section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album: Album object with RYM descriptors.
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
        Build Line objects for descriptors.

        Args:
            context: Rendering context with font configuration.

        Returns:
            List of Line objects representing descriptors text.
        """
        lines: list[Line] = []

        # Add descriptors
        if self.album.rym_descriptors:
            # Header line (bold, fixed size)
            lines.append(Line(
                text="Descriptors:",
                point_size=self.font_size,
                leading_ratio=self.leading_ratio,
                fixed_size=True,  # Don't reduce header
                font_family=f"{context.theme.font_family}-Bold"
            ))

            # Descriptors text (can wrap and compress)
            descriptor_text = ", ".join(self.album.rym_descriptors)
            lines.append(Line(
                text=descriptor_text,
                point_size=self.font_size,
                leading_ratio=self.leading_ratio,
                fixed_size=False,  # Allow size reduction
                font_family=context.theme.font_family
            ))

        return lines

    def render(self, context: RendererContext) -> None:
        """Render descriptors using centralized rendering."""
        c = context.canvas

        # Establish local coordinate system
        c.saveState()
        c.translate(context.x, context.y)

        # Use custom padding if provided, otherwise use larger padding for genre panel
        if self.padding_override is not None:
            padding = inches_to_points(self.padding_override)
        else:
            # Use larger padding for genre panel (0.15" = 10.8 points instead of default ~7.2 points)
            padding = inches_to_points(0.15)  # Convert inches to points

        # Create TextBounds for fitting and rendering (using relative coordinates)
        bounds = TextBounds.from_relative_context(context, padding)

        # Build Line objects
        lines = self._build_text_lines(context)

        # If no descriptors, nothing to render
        if not lines:
            c.restoreState()
            return

        # Fit all text within constraints
        # Uses canonical formula (glyph_height_adjusted=True by default)
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=bounds.width,
            max_height=bounds.height,
            min_horizontal_scale=0.9,  # Minimal compression - prefer wrapping
            split_max=15,  # Allow many splits for natural wrapping
            min_point_size=5.0
        )

        # Render using centralized canonical renderer
        render_fitted_text(
            fitted_lines,
            c,
            bounds,
            context,
            alignment="left"
        )

        c.restoreState()
