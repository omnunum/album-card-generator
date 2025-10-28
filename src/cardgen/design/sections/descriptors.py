"""Descriptors section implementation."""

from reportlab.lib.colors import Color

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions
from cardgen.utils.text import Line, fit_text_block


class DescriptorsSection(CardSection):
    """Section displaying RYM descriptors."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album: Album,
        font_size: float = 7.0,
        padding_override: float | None = None,
    ) -> None:
        """
        Initialize descriptors section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album: Album object with RYM descriptors.
            font_size: Font size in points (default: 7.0).
            padding_override: Custom padding in inches. If None, uses theme default.
        """
        super().__init__(name, dimensions)
        self.album = album
        self.font_size = font_size
        self.padding_override = padding_override

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
            # Descriptors text (can wrap and compress)
            descriptor_text = "Descriptors: " + ", ".join(self.album.rym_descriptors)
            lines.append(Line(
                text=descriptor_text,
                point_size=self.font_size,
                leading_ratio=0.4,
                fixed_size=False,  # Allow size reduction
                font_family=context.font_config.family
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
        Render fitted text lines for descriptors.

        Args:
            context: Rendering context.
            fitted_lines: Fitted Line objects from fit_text_block.
            start_y: Starting y position (top of text area).
            padding: Horizontal padding.
        """
        c = context.canvas
        text_y = start_y

        for fitted_line in fitted_lines:
            # Skip empty lines (spacing)
            if not fitted_line.text:
                text_y -= fitted_line.point_size + (fitted_line.point_size * fitted_line.leading_ratio)
                continue

            c.setFillColor(Color(*context.color_scheme.text))

            # Draw descriptor text
            c.setFont(fitted_line.font_family, fitted_line.point_size)
            if fitted_line.horizontal_scale < 1.0:
                c.saveState()
                c.translate(context.x + padding, text_y)
                c.scale(fitted_line.horizontal_scale, 1.0)
                c.drawString(0, 0, fitted_line.text)
                c.restoreState()
            else:
                c.drawString(context.x + padding, text_y, fitted_line.text)

            # Move down for next line
            text_y -= fitted_line.point_size + (fitted_line.point_size * fitted_line.leading_ratio)

    def render(self, context: RendererContext) -> None:
        """Render descriptors using fit_text_block."""
        c = context.canvas

        # Use custom padding if provided, otherwise use larger padding for genre panel
        if self.padding_override is not None:
            padding = self.padding_override * 72  # Convert inches to points
        else:
            # Use larger padding for genre panel (0.15" = 10.8 points instead of default ~7.2 points)
            padding = 0.15 * 72  # Convert inches to points

        # Calculate available space
        available_height = context.height - (padding * 2)
        available_width = context.width - (padding * 2)

        # Build Line objects
        lines = self._build_text_lines(context)

        # If no descriptors, nothing to render
        if not lines:
            return

        # Fit all text within constraints
        # Use minimal compression and allow many splits for natural wrapping
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=available_width,
            max_height=available_height,
            min_horizontal_scale=0.9,  # Minimal compression - prefer wrapping
            split_max=15,  # Allow many splits for natural wrapping
            min_point_size=5.0
        )

        # Render fitted lines
        start_y = context.y + context.height - padding - fitted_lines[0].point_size
        self._render_fitted_lines(context, fitted_lines, start_y, padding)
