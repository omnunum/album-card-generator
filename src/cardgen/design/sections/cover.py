"""Cover section implementation."""

from io import BytesIO

from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader

from cardgen.design.base import CardSection, RendererContext
from cardgen.render.image import resize_and_crop_cover
from cardgen.utils.dimensions import Dimensions


class CoverSection(CardSection):
    """Front cover section with album art, title, and artist."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        cover_art: bytes,
        title: str,
        artist: str,
    ) -> None:
        """
        Initialize cover section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            cover_art: Raw image data for album art.
            title: Album title.
            artist: Artist name.
        """
        super().__init__(name, dimensions)
        self.cover_art = cover_art
        self.title = title
        self.artist = artist

    def render(self, context: RendererContext) -> None:
        """Render front cover with album art."""
        c = context.canvas

        # Calculate dimensions for square album art (leaving room for text)
        text_height = 60  # Reserve space for title and artist
        art_size = min(
            context.width - (context.padding * 2),
            context.height - text_height - (context.padding * 3),
        )

        # Center album art horizontally
        art_x = context.x + (context.width - art_size) / 2
        art_y = context.y + context.height - art_size - context.padding

        # Resize and crop album art
        target_px = int((art_size / 72) * context.dpi)
        processed_img = resize_and_crop_cover(self.cover_art, (target_px, target_px))

        # Save to temporary bytes buffer and create ImageReader
        img_buffer = BytesIO()
        processed_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)

        # Draw image
        c.drawImage(
            img_reader,
            art_x,
            art_y,
            width=art_size,
            height=art_size,
            preserveAspectRatio=True,
        )

        # Draw title and artist below album art
        c.setFillColor(Color(*context.color_scheme.text))

        # Artist
        c.setFont(context.font_config.family, context.font_config.artist_size)
        text_y = art_y - context.padding - context.font_config.artist_size
        c.drawCentredString(context.x + context.width / 2, text_y, self.artist)

        # Title
        c.setFont(
            f"{context.font_config.family}-Bold", context.font_config.title_size
        )
        text_y -= context.font_config.title_size + 4
        c.drawCentredString(context.x + context.width / 2, text_y, self.title)
