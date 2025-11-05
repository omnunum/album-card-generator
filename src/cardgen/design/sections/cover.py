"""Cover section implementation."""

import io
import logging
import os

import requests
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader
from svglib.svglib import svg2rlg

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import SAFE_MARGIN, Dimensions, inches_to_points, points_to_inches
from cardgen.utils.text import Line, fit_text_block, TextBounds, render_fitted_text


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
        leading_ratio: float = 0.27,
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
            leading_ratio: Leading ratio for text (default: 0.27).
                          Updated from 0.2 to account for canonical formula using adjusted_point_size.
        """
        super().__init__(name, dimensions)
        self.album_art = album_art
        self.title = title
        self.artist = artist
        self.show_dolby_logo = show_dolby_logo
        self.leading_ratio = leading_ratio

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
            context.theme.title_font
            if context.theme.title_font
            else f"{context.theme.font_family}-Bold"
        )

        # Determine artist font (use specific font if configured, else default to regular)
        artist_font = (
            context.theme.artist_font
            if context.theme.artist_font
            else context.theme.font_family
        )

        # Title line (bold) - start at theme max font size to maximize text size
        lines.append(Line(
            text=self.title,
            point_size=context.theme.album_title_font_size,  # Max font size from theme, will auto-reduce to fit
            leading_ratio=self.leading_ratio,
            fixed_size=False,
            font_family=title_font
        ))

        # Artist line (regular) - start at theme max font size to maximize text size
        lines.append(Line(
            text=self.artist,
            point_size=context.theme.artist_font_size,  # Max font size from theme, will auto-reduce to fit
            leading_ratio=self.leading_ratio,
            fixed_size=False,
            font_family=artist_font
        ))

        return lines

    def render(self, context: RendererContext) -> None:
        """Render front cover with album art and text based on cover_art_mode."""
        mode = context.theme.cover_art_mode

        if mode == "compact":
            self._render_compact_mode(context)
        else:
            self._render_standard_mode(context)

    def _render_standard_mode(self, context: RendererContext) -> None:
        """Render cover with art on top and text below (square or fullscale mode)."""
        c = context.canvas
        mode = context.theme.cover_art_mode
        align = context.theme.cover_art_align

        # Reserve minimum space for text
        min_text_height = 90

        if mode == "fullscale":
            # Art fills full height with horizontal crop/alignment
            art_height = context.height - min_text_height
            art_width = context.width
        else:  # "square"
            # Art is square, centered
            art_size = min(context.width, context.height - min_text_height)
            art_width = art_size
            art_height = art_size

        # Art at top, text at bottom
        art_x = context.x
        art_y = context.y + (context.height - art_height)
        text_height = context.height - art_height

        # Render album art
        if self.album_art:
            art_dims = Dimensions(width=art_width/72, height=art_height/72, dpi=context.dpi)
            pixel_dims = art_dims.to_pixels()

            if mode == "fullscale":
                processed_img = self.album_art.resize_and_crop(
                    (pixel_dims.width, pixel_dims.height), mode="fullscale", align=align
                )
            else:
                processed_img = self.album_art.resize_and_crop(
                    (pixel_dims.width, pixel_dims.width), mode="square"
                )

            img_reader = AlbumArt.pil_to_image_reader(processed_img)
            c.drawImage(
                img_reader, art_x, art_y,
                width=art_width, height=art_height,
                preserveAspectRatio=True,
            )

        # Render text section below art
        text_context = RendererContext(
            canvas=c,
            x=context.x,
            y=context.y,
            width=context.width,
            height=text_height,
            theme=context.theme,
            padding=inches_to_points(context.theme.cover_title_padding),
            dpi=context.dpi
        )
        self._render_text_section(text_context)

    def _render_compact_mode(self, context: RendererContext) -> None:
        """Render cover in compact mode: art left (2"), text right (0.5") rotated."""
        c = context.canvas

        # Split horizontally: 2" art + 0.5" text = 2.5" total
        text_width_inches = 0.5
        text_width_pts = inches_to_points(text_width_inches)
        art_width = context.width - text_width_pts

        # Render album art (full bleed vertically)
        if self.album_art:
            art_dims = Dimensions(
                width=points_to_inches(art_width), 
                height=points_to_inches(context.height), 
                dpi=context.dpi
            )
            pixel_dims = art_dims.to_pixels()
            processed_img = self.album_art.resize_and_crop(
                (pixel_dims.width, pixel_dims.height),
                mode="fullscale",
                align="center"
            )
            img_reader = AlbumArt.pil_to_image_reader(processed_img)
            c.drawImage(
                img_reader,
                context.x, context.y,
                width=art_width, height=context.height,
                preserveAspectRatio=True,
            )

        # Render rotated text section on the right
        c.saveState()
        c.translate(context.x + context.width, context.y)
        c.rotate(90)

        # Create context for rotated text section (width and height are swapped)
        text_context = RendererContext(
            canvas=c,
            x=0,
            y=0,
            width=context.height,  # Original height becomes width after rotation
            height=text_width_pts,  # Original text width becomes height
            theme=context.theme,
            padding=inches_to_points(context.theme.cover_title_padding) / 2,
            dpi=context.dpi
        )
        self._render_text_section(text_context)
        c.restoreState()

    def _render_text_section(self, context: RendererContext) -> None:
        """Render text (title/artist) and logos in the given context bounds."""
        c = context.canvas

        # Create TextBounds for fitting and rendering (using absolute coordinates)
        bounds = TextBounds.from_context(context, inches_to_points(context.theme.cover_title_padding))

        # Build and fit text lines
        lines = self._build_text_lines(context)
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=bounds.width,
            max_height=bounds.height,
            min_horizontal_scale=0.75,
            split_max=2,
            min_point_size=6.0 if context.theme.cover_art_mode == "compact" else 8.0
        )

        # Render using centralized canonical renderer with center alignment
        render_fitted_text(
            fitted_lines,
            c,
            bounds,
            context,
            alignment="center"
        )

        # Skip logos in compact mode (not enough space)
        if context.theme.cover_art_mode == "compact":
            return

        # Render Dolby logo if requested
        if self.show_dolby_logo:
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets')
            logo_path = os.path.join(assets_dir, 'dolby-b-full-white.svg')

            if os.path.exists(logo_path):
                drawing = svg2rlg(logo_path)
                if drawing:
                    logo_padding = inches_to_points(1/16)
                    logo_width = context.width / 3
                    aspect_ratio = drawing.width / drawing.height
                    logo_height = logo_width / aspect_ratio

                    scale_factor = logo_width / drawing.width
                    drawing.width = logo_width
                    drawing.height = logo_height
                    drawing.scale(scale_factor, scale_factor)

                    logo_x = context.x + logo_padding
                    logo_y = context.y + logo_padding
                    renderPDF.draw(drawing, c, logo_x, logo_y)

        # Render label logo if specified
        if context.theme.label_logo:
            try:
                if context.theme.label_logo.startswith(('http://', 'https://')):
                    response = requests.get(context.theme.label_logo, timeout=10)
                    response.raise_for_status()
                    logo_bytes = response.content
                else:
                    with open(context.theme.label_logo, 'rb') as f:
                        logo_bytes = f.read()

                from PIL import Image
                img = Image.open(io.BytesIO(logo_bytes))

                logo_max_pts = 35
                aspect_ratio = img.width / img.height

                if img.width >= img.height:
                    logo_width = logo_max_pts
                    logo_height = logo_max_pts / aspect_ratio
                else:
                    logo_height = logo_max_pts
                    logo_width = logo_max_pts * aspect_ratio

                img_reader = ImageReader(img)
                logo_padding = inches_to_points(1/16)
                logo_x = context.x + context.width - logo_width - logo_padding
                logo_y = context.y + logo_padding

                c.drawImage(
                    img_reader, logo_x, logo_y,
                    width=logo_width, height=logo_height,
                    mask='auto', preserveAspectRatio=True,
                )
            except (requests.RequestException, OSError, Image.UnidentifiedImageError, ValueError) as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load or render label logo '{context.theme.label_logo}': {e}")
