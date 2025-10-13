"""Metadata section implementation."""

from reportlab.lib.colors import Color

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions


class MetadataSection(CardSection):
    """Metadata section with vertical text (genre, label, year, etc.)."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        items: list[str],
    ) -> None:
        """
        Initialize metadata section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            items: List of metadata items to display.
        """
        super().__init__(name, dimensions)
        self.items = items

    def render(self, context: RendererContext) -> None:
        """Render metadata items vertically."""
        c = context.canvas

        # Combine items with separator
        metadata_text = " • ".join(self.items)

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
            metadata_text,
            context.font_config.family,
            context.font_config.metadata_size,
        )
        c.drawString(
            -text_width / 2, -context.font_config.metadata_size / 2, metadata_text
        )

        c.restoreState()
