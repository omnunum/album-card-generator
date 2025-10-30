"""Cover section implementation."""

import os

from reportlab.graphics import renderPDF
from reportlab.lib.colors import Color
from svglib.svglib import svg2rlg

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import SAFE_MARGIN, Dimensions, inches_to_points
from cardgen.utils.text import Line, fit_text_block


class CoverSection(CardSection):
    """Front cover section with album art, title, and artist."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album_art: AlbumArt | None,
        title: str,
        artist: str,
        show_dolby_logo: bool = False,
    ) -> None:
        """
        Initialize cover section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album_art: AlbumArt object for image processing.
            title: Album title.
            artist: Artist name.
            show_dolby_logo: Whether to show the Dolby NR logo on the cover.
        """
        super().__init__(name, dimensions)
        self.album_art = album_art
        self.title = title
        self.artist = artist
        self.show_dolby_logo = show_dolby_logo

    def _build_text_lines(self, context: RendererContext) -> list[Line]:
        """
        Build Line objects for title and artist.

        Args:
            context: Rendering context with font configuration.

        Returns:
            List of Line objects (title first, then artist).
        """
        lines: list[Line] = []

        # Determine title font (use specific font if configured, else default to Bold)
        title_font = (
            context.font_config.title_font
            if context.font_config.title_font
            else f"{context.font_config.family}-Bold"
        )

        # Determine artist font (use specific font if configured, else default to regular)
        artist_font = (
            context.font_config.artist_font
            if context.font_config.artist_font
            else context.font_config.family
        )

        # Title line (bold) - start large to maximize text size
        lines.append(Line(
            text=self.title,
            point_size=40,  # Start large, will auto-reduce to fit
            leading_ratio=0.2,  # Spacing after title
            fixed_size=False,
            font_family=title_font
        ))

        # Artist line (regular) - start large to maximize text size
        lines.append(Line(
            text=self.artist,
            point_size=30,  # Start large, will auto-reduce to fit
            leading_ratio=0.2,  # No spacing after (last line)
            fixed_size=False,
            font_family=artist_font
        ))

        return lines

    def _render_fitted_lines_centered(
        self,
        context: RendererContext,
        fitted_lines: list[Line],
        start_y: float,
        available_width: float
    ) -> None:
        """
        Render fitted text lines centered horizontally.

        Args:
            context: Rendering context.
            fitted_lines: Fitted Line objects from fit_text_block.
            start_y: Starting y position (top of text area).
            available_width: Available width for centering.
        """
        c = context.canvas
        text_y = start_y

        for fitted_line in fitted_lines:
            c.setFont(fitted_line.font_family, fitted_line.point_size)
            c.setFillColor(Color(*context.color_scheme.text))

            # Calculate text width with scaling
            base_width = c.stringWidth(fitted_line.text, fitted_line.font_family, fitted_line.point_size)
            scaled_width = base_width * fitted_line.horizontal_scale

            # Center the text
            center_x = context.x + context.width / 2

            # Draw text with horizontal scaling if needed
            if fitted_line.horizontal_scale < 1.0:
                c.saveState()
                c.translate(center_x - scaled_width / 2, text_y)
                c.scale(fitted_line.horizontal_scale, 1.0)
                c.drawString(0, 0, fitted_line.text)
                c.restoreState()
            else:
                c.drawCentredString(center_x, text_y, fitted_line.text)

            # Move down for next line
            text_y -= fitted_line.point_size + (fitted_line.point_size * fitted_line.leading_ratio)

    def render(self, context: RendererContext) -> None:
        """Render front cover with album art using fit_text_block."""
        c = context.canvas

        # Get cover art mode and alignment from theme
        mode = context.color_scheme.cover_art_mode
        align = context.color_scheme.cover_art_align

        # Reserve minimum space for text (will use all remaining space after art)
        min_text_height = 90  # Minimum space needed for large text + padding

        if mode == "fullscale":
            # Fullscale mode: art fills full height with horizontal crop/alignment
            # Calculate art height, leaving minimum space for text
            art_height = context.height - min_text_height
            art_width = context.width

            # Position album art at left edge, extending to top
            art_x = context.x
            art_y = context.y + context.height - art_height

            # Text gets all remaining space
            text_height = context.height - art_height

            # Resize and crop album art with alignment
            art_dims = Dimensions(width=art_width/72, height=art_height/72, dpi=context.dpi)
            pixel_dims = art_dims.to_pixels()
            processed_img = self.album_art.resize_and_crop(
                (pixel_dims.width, pixel_dims.height), mode="fullscale", align=align
            )
        else:
            # Square mode (default): art is square, centered
            # Calculate square art size, leaving minimum space for text
            art_size = min(
                context.width,  # Full width, no padding
                context.height - min_text_height,  # Leave space for text
            )

            # Position album art at left edge, extending to top
            art_x = context.x
            art_y = context.y + context.height - art_size
            art_width = art_size
            art_height = art_size

            # Text gets all remaining space
            text_height = context.height - art_size

            # Resize and crop album art
            art_dims = Dimensions(width=art_size/72, height=art_size/72, dpi=context.dpi)
            pixel_dims = art_dims.to_pixels()
            processed_img = self.album_art.resize_and_crop((pixel_dims.width, pixel_dims.width), mode="square")

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

        # Calculate available space for text (respect safe margins)
        safe_margin_pts = inches_to_points(SAFE_MARGIN)
        available_text_width = context.width - (context.padding * 2) - (safe_margin_pts * 2)
        available_text_height = text_height - (context.padding * 2)

        # Build text lines
        lines = self._build_text_lines(context)

        # Fit text within available space
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=available_text_width,
            max_height=available_text_height,
            min_horizontal_scale=0.85,
            split_max=2,  # Allow more splitting for long titles
            min_point_size=8.0  # Keep text readable on cover
        )

        # Render fitted lines centered
        start_y = art_y - context.padding - fitted_lines[0].point_size
        self._render_fitted_lines_centered(context, fitted_lines, start_y, available_text_width)

        # Render Dolby logo if requested
        if self.show_dolby_logo:
            # Load the white Dolby logo SVG
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets')
            logo_path = os.path.join(assets_dir, 'dolby-b-full-white.svg')

            if os.path.exists(logo_path):
                drawing = svg2rlg(logo_path)

                if drawing:
                    # Calculate logo dimensions (1/3 of panel width, maintaining aspect ratio)
                    logo_padding = inches_to_points(1/16)
                    logo_width = context.width / 3
                    aspect_ratio = drawing.width / drawing.height
                    logo_height = logo_width / aspect_ratio

                    # Scale the drawing
                    scale_factor = logo_width / drawing.width
                    drawing.width = logo_width
                    drawing.height = logo_height
                    drawing.scale(scale_factor, scale_factor)

                    # Position logo at bottom left with padding
                    logo_x = context.x + logo_padding
                    logo_y = context.y + logo_padding

                    # Render the logo
                    renderPDF.draw(drawing, c, logo_x, logo_y)
