"""Spine section implementation."""

from reportlab.lib.colors import Color

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions


class SpineSection(CardSection):
    """Spine section with vertical text (artist, album, year)."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        text_lines: list[str],
    ) -> None:
        """
        Initialize spine section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            text_lines: List of text lines to display.
        """
        super().__init__(name, dimensions)
        self.text_lines = text_lines

    def render(self, context: RendererContext) -> None:
        """Render spine with vertical text."""
        c = context.canvas

        # Combine text with separator
        spine_text = " • ".join(self.text_lines)

        c.setFillColor(Color(*context.color_scheme.text))
        c.setFont(context.font_config.family, context.font_config.metadata_size)

        # Save state, rotate, and draw vertical text
        c.saveState()

        # Rotate 90 degrees counterclockwise and position text
        c.translate(
            context.x + context.width / 2, context.y + context.height / 2
        )
        c.rotate(90)

        # Draw centered text
        text_width = c.stringWidth(
            spine_text, context.font_config.family, context.font_config.metadata_size
        )
        c.drawString(
            -text_width / 2, -context.font_config.metadata_size / 2, spine_text
        )

        c.restoreState()
