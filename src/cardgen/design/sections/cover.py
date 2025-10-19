"""Cover section implementation."""

from io import BytesIO

from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader

from cardgen.design.base import CardSection, RendererContext
from cardgen.render.image import resize_and_crop_cover, resize_and_crop_cover_fullscale
from cardgen.types import CoverArtAlign, CoverArtMode
from cardgen.utils.dimensions import SAFE_MARGIN, Dimensions, inches_to_points
from cardgen.utils.text import calculate_max_font_size


class CoverSection(CardSection):
    """Front cover section with album art, title, and artist."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        cover_art: bytes,
        title: str,
        artist: str,
        cover_art_mode: CoverArtMode = "square",
        cover_art_align: CoverArtAlign = "center",
    ) -> None:
        """
        Initialize cover section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            cover_art: Raw image data for album art.
            title: Album title.
            artist: Artist name.
            cover_art_mode: Display mode - "square" or "fullscale".
            cover_art_align: Horizontal alignment for fullscale - "center", "left", or "right".
        """
        super().__init__(name, dimensions)
        self.cover_art = cover_art
        self.title = title
        self.artist = artist
        self.cover_art_mode = cover_art_mode
        self.cover_art_align = cover_art_align

    def render(self, context: RendererContext) -> None:
        """Render front cover with album art."""
        c = context.canvas

        if self.cover_art_mode == "fullscale":
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
            processed_img = resize_and_crop_cover_fullscale(
                self.cover_art, (target_width_px, target_height_px), align=self.cover_art_align
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
            words = self.artist.split()
            lines = []
            current_line = []

            for word in words:
                test_line = " ".join(current_line + [word])
                test_width = c.stringWidth(test_line, context.font_config.family, artist_size)

                if test_width <= available_text_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                    else:
                        # Single word too long, force it
                        lines.append(word)

            if current_line:
                lines.append(" ".join(current_line))

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

        # Title - use dynamic sizing to fit within panel width
        title_font_name = f"{context.font_config.family}-Bold"

        # Calculate optimal title size
        title_size = calculate_max_font_size(
            c, self.title, title_font_name, available_text_width,
            context.font_config.title_size * 2,  # Allow up to 2x normal size
            min_size=8, max_size=context.font_config.title_size + 4,
            safe_margin=0  # Already accounted for above
        )

        # Check if title fits on one line
        title_width = c.stringWidth(self.title, title_font_name, title_size)

        if title_width <= available_text_width:
            # Single line title
            c.setFont(title_font_name, title_size)
            text_y -= title_size + 4
            c.drawCentredString(context.x + context.width / 2, text_y, self.title)
            return
        
        # Multi-line title - split at word boundaries
        words = self.title.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            test_width = c.stringWidth(test_line, title_font_name, title_size)

            if test_width <= available_text_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # Single word too long, force it
                    lines.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        # Draw each line centered
        c.setFont(title_font_name, title_size)
        line_spacing = 2
        total_title_height = len(lines) * title_size + (len(lines) - 1) * line_spacing
        text_y -= total_title_height + 4

        for i, line in enumerate(lines):
            line_y = text_y + total_title_height - (i * (title_size + line_spacing))
            c.drawCentredString(context.x + context.width / 2, line_y, line)
