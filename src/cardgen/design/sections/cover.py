"""Cover section implementation."""

from reportlab.lib.colors import Color

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import SAFE_MARGIN, Dimensions, inches_to_points
from cardgen.utils.text import calculate_max_font_size, wrap_text_to_width


class CoverSection(CardSection):
    """Front cover section with album art, title, and artist."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album_art: AlbumArt | None,
        title: str,
        artist: str,
    ) -> None:
        """
        Initialize cover section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album_art: AlbumArt object for image processing.
            title: Album title.
            artist: Artist name.
        """
        super().__init__(name, dimensions)
        self.album_art = album_art
        self.title = title
        self.artist = artist

    def render(self, context: RendererContext) -> None:
        """Render front cover with album art."""
        c = context.canvas

        # Get cover art mode and alignment from theme
        mode = context.color_scheme.cover_art_mode
        align = context.color_scheme.cover_art_align

        if mode == "fullscale":
            # Fullscale mode: art fills full height with horizontal crop/alignment
            text_height = 60  # Reserve space for title and artist at bottom

            # Art fills full panel width and full available height
            art_width = context.width
            art_height = context.height - text_height

            # Position album art at left edge, extending to top
            art_x = context.x
            art_y = context.y + context.height - art_height

            # Resize and crop album art with alignment
            target_width_px = int((art_width / 72) * context.dpi)
            target_height_px = int((art_height / 72) * context.dpi)
            processed_img = self.album_art.resize_and_crop(
                (target_width_px, target_height_px), mode="fullscale", align=align
            )
        else:
            # Square mode (default): art is square, centered
            text_height = 60  # Reserve space for title and artist at bottom

            # Art fills full panel width (no side padding) and extends to top
            art_size = min(
                context.width,  # Full width, no padding
                context.height - text_height,  # Fill from top down to text area
            )

            # Position album art at left edge, extending to top
            art_x = context.x
            art_y = context.y + context.height - art_size
            art_width = art_size
            art_height = art_size

            # Resize and crop album art
            target_px = int((art_size / 72) * context.dpi)
            processed_img = self.album_art.resize_and_crop((target_px, target_px), mode="square")

        # Convert PIL image to ImageReader
        img_reader = AlbumArt.pil_to_image_reader(processed_img)

        # Draw image
        c.drawImage(
            img_reader,
            art_x,
            art_y,
            width=art_width,
            height=art_height,
            preserveAspectRatio=True,
        )

        # Draw title and artist below album art
        c.setFillColor(Color(*context.color_scheme.text))

        # Calculate available width for text (respect safe margins)
        safe_margin_pts = inches_to_points(SAFE_MARGIN)
        available_text_width = context.width - (context.padding * 2) - (safe_margin_pts * 2)

        # Artist - with word wrapping if needed
        artist_size = context.font_config.artist_size
        text_y = art_y - context.padding - artist_size

        artist_width = c.stringWidth(self.artist, context.font_config.family, artist_size)

        if artist_width <= available_text_width:
            # Single line artist
            c.setFont(context.font_config.family, artist_size)
            c.drawCentredString(context.x + context.width / 2, text_y, self.artist)
        else:
            # Multi-line artist - split at word boundaries
            lines = wrap_text_to_width(
                c, self.artist, available_text_width, context.font_config.family, artist_size,
                mode="multi_line"
            )

            # Draw each line centered
            c.setFont(context.font_config.family, artist_size)
            line_spacing = 2
            total_artist_height = len(lines) * artist_size + (len(lines) - 1) * line_spacing

            # Adjust text_y for multi-line artist
            for i, line in enumerate(lines):
                line_y = text_y - (i * (artist_size + line_spacing))
                c.drawCentredString(context.x + context.width / 2, line_y, line)

            # Update text_y to account for multiple lines
            text_y -= total_artist_height

        # Title - use configured title size
        title_font_name = f"{context.font_config.family}-Bold"
        title_size = context.font_config.title_size

        # Check if title fits on one line
        title_width = c.stringWidth(self.title, title_font_name, title_size)

        if title_width <= available_text_width:
            # Single line title
            c.setFont(title_font_name, title_size)
            text_y -= title_size + 4
            c.drawCentredString(context.x + context.width / 2, text_y, self.title)
            return

        # Multi-line title - split at word boundaries
        lines = wrap_text_to_width(
            c, self.title, available_text_width, title_font_name, title_size,
            mode="multi_line"
        )

        # Draw each line centered
        c.setFont(title_font_name, title_size)
        line_spacing = 2
        total_title_height = len(lines) * title_size + (len(lines) - 1) * line_spacing
        text_y -= total_title_height + 4

        for i, line in enumerate(lines):
            line_y = text_y + total_title_height - (i * (title_size + line_spacing))
            c.drawCentredString(context.x + context.width / 2, line_y, line)
