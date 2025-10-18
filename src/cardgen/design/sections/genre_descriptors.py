"""Genre and descriptors section implementation."""

from reportlab.lib.colors import Color

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions
from cardgen.utils.genres import build_genre_tree


class GenreDescriptorsSection(CardSection):
    """Section displaying full genre tree and RYM descriptors."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album: Album,
        font_size: float = 7.0,
        padding_override: float | None = None,
    ) -> None:
        """
        Initialize genre descriptors section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album: Album object with genres and descriptors.
            font_size: Font size in points (default: 7.0).
            padding_override: Custom padding in inches. If None, uses theme default.
        """
        super().__init__(name, dimensions)
        self.album = album
        self.font_size = font_size
        self.padding_override = padding_override

    def render(self, context: RendererContext) -> None:
        """Render genre tree and descriptors as horizontal text (like tracklist)."""
        c = context.canvas

        # Build genre tree
        genre_tree = build_genre_tree(self.album.genres) if self.album.genres else ""

        # Format descriptors
        descriptor_text = ""
        if self.album.rym_descriptors:
            descriptors = self.album.rym_descriptors
            descriptor_text = "Descriptors: " + ", ".join(descriptors)

        # Set up drawing
        c.setFillColor(Color(*context.color_scheme.text))

        # Use custom padding if provided, otherwise use larger padding for genre panel
        if self.padding_override is not None:
            padding = self.padding_override * 72  # Convert inches to points
        else:
            # Use larger padding for genre panel (0.15" = 10.8 points instead of default ~7.2 points)
            padding = 0.15 * 72  # Convert inches to points

        line_height = self.font_size * 1.4  # 40% line spacing for better readability

        # Start from top (no rotation, regular horizontal layout)
        text_y = context.y + context.height - padding - self.font_size
        available_width = context.width - (2 * padding)

        # Draw genre tree
        if genre_tree:
            c.setFont(f"{context.font_config.family}-Bold", self.font_size)
            c.drawString(context.x + padding, text_y, "Genre Tree:")
            text_y -= line_height

            # Use monospace font for the genre tree ASCII art
            c.setFont(context.font_config.monospace_family, self.font_size)
            genre_lines = genre_tree.split("\n")
            for line in genre_lines:
                if text_y < context.y + padding:
                    break
                c.drawString(context.x + padding, text_y, line)
                text_y -= line_height

        # Add spacing before descriptors
        if genre_tree and descriptor_text:
            text_y -= line_height * 0.5

        # Draw descriptors
        if descriptor_text and text_y >= context.y + padding:
            c.setFont(context.font_config.family, self.font_size)
            # Word wrap the descriptor text
            wrapped_lines = self._wrap_text(c, descriptor_text, available_width, context.font_config.family, self.font_size)
            for line in wrapped_lines:
                if text_y < context.y + padding:
                    break
                c.drawString(context.x + padding, text_y, line)
                text_y -= line_height

    def _wrap_text(self, c, text: str, max_width: float, font_family: str, font_size: float) -> list[str]:
        """
        Wrap text to fit within max_width.

        Args:
            c: Canvas for measuring text width.
            text: Text to wrap.
            max_width: Maximum width in points.
            font_family: Font family name.
            font_size: Font size in points.

        Returns:
            List of wrapped lines.
        """
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            width = c.stringWidth(test_line, font_family, font_size)

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines
