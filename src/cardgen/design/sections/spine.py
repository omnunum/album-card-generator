"""Spine section implementation."""

import os
from typing import Optional

from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics import renderPDF
from reportlab.lib.colors import Color
from svglib.svglib import svg2rlg

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import Dimensions, inches_to_points
from cardgen.utils.text import Line, fit_text_block, calculate_total_height




class SpineSection(CardSection):
    """Spine section with vertical text (artist, album, year) and optional album art."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        text_lines: list[str],
        album_art_left: Optional[AlbumArt] = None,
        album_art_right: Optional[AlbumArt] = None,
        show_dolby_logo: bool = False,
    ) -> None:
        """
        Initialize spine section with modular components.

        Components are laid out left-to-right when spine text is properly oriented:
        [album_art_left] [text_lines] [dolby_logo] [album_art_right]

        Args:
            name: Section name.
            dimensions: Section dimensions.
            text_lines: List of text strings for spine (will auto-size and can split).
            album_art_left: Optional AlbumArt for left side of spine.
            album_art_right: Optional AlbumArt for right side of spine.
            show_dolby_logo: Whether to show the Dolby NR logo on the spine.
        """
        super().__init__(name, dimensions)
        self.text_lines: list[str] = text_lines
        self.album_art_left = album_art_left
        self.album_art_right = album_art_right
        self.show_dolby_logo = show_dolby_logo

    def _build_text_lines(self, context: RendererContext) -> list[Line]:
        """
        Build Line objects for spine text.

        For double albums (>3 items), creates multiple lines (one per album).
        For single albums, creates a single line.

        Args:
            context: Rendering context with font configuration.

        Returns:
            List of Line objects (one per album for double albums).
        """
        formatted_lines : list[Line] = []
        # Split text items into chunks (one per line)
        for line in self.text_lines:
            formatted_lines.append(Line(
                text=line,
                point_size=30,  # Start large, fit_text_block will reduce if needed
                leading_ratio=0.35,  # Spacing between lines
                fixed_size=False,  # Allow size reduction
                font_family=f"{context.theme.font_family}-Bold"
            ))

        return formatted_lines

    def render(self, context: RendererContext) -> None:
        """
        Render spine with modular components that auto-adjust layout.

        Layout (left to right when rotated): [album_art_left] [text] [dolby_logo] [album_art_right]
        """
        # Component sizes
        component_gap = 6  # Gap points between components

        # Calculate album art sizes (0.5" square if present)
        art_left_size = inches_to_points(0.5) if self.album_art_left else 0
        art_right_size = inches_to_points(0.5) if self.album_art_right else 0

        # Calculate Dolby logo size (half spine width if present)
        dolby_logo_length = (context.width / 2) if self.show_dolby_logo else 0

        # Calculate gaps (only add gap if component exists)
        gap_left = component_gap
        gap_right = component_gap if self.album_art_right else 0
        gap_dolby = component_gap if self.show_dolby_logo else 0

        # Calculate total consumed space
        total_consumed = (
            art_left_size 
            + gap_left 
            + dolby_logo_length
            + gap_dolby 
            + art_right_size 
            + gap_right
        )

        # Available space for text (after rotation: height becomes length)
        available_length = context.height - total_consumed
        available_width = context.width

        # Draw white border around non-album-art area
        self._render_border(context, art_left_size, art_right_size)

        c = context.canvas
        c.saveState()
        c.translate(context.x + inches_to_points(0.5), context.y)
        c.rotate(90)
        # 1. Render left album art if present
        if self.album_art_left:
            self._render_album_art(
                context, self.album_art_left,
            )
            c.translate(art_left_size, 0)

        c.translate(gap_left, 0)
        
        # 2. Render text (will be centered in available space)
        self._render_text(context, available_length, available_width)
        c.translate(available_length, 0)

        # 3. Render Dolby logo if present
        if self.show_dolby_logo:
            c.translate(gap_dolby, 0)
            c.saveState()
            c.translate(0, (available_width - dolby_logo_length) / 2)
            self._render_dolby_logo(
                context,
                logo_length=dolby_logo_length
            )
            c.restoreState()
            c.translate(dolby_logo_length, 0)

        # 4. Render right album art if present
        if self.album_art_right:
            c.translate(gap_right, 0)
            self._render_album_art(
                context, self.album_art_right,
            )

        context.canvas.restoreState()

    def _render_album_art(
        self,
        context: RendererContext,
        album_art: AlbumArt,
    ) -> None:
        """Render album art at specified position."""
        c = context.canvas
        art_dims = Dimensions(width=0.5, height=0.5, dpi=context.dpi)
        point_dims = art_dims.to_points()
        pixel_dims = art_dims.to_pixels()

        processed_img = album_art.resize_and_crop(
            (pixel_dims.width, pixel_dims.height),
            mode="square"
        )

        img_reader = album_art.to_image_reader(processed_img)
        c.drawImage(
            img_reader,
            0, 0,  # Center at origin
            width=point_dims.width, height=point_dims.height,
            preserveAspectRatio=True
        )

    def _render_dolby_logo(
        self,
        context: RendererContext,
        logo_length: float
    ) -> None:
        """Render Dolby logo at specified position."""
        c = context.canvas
        assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'assets'
        )
        logo_path = os.path.join(assets_dir, 'dolby-b-logo-white.svg')

        if os.path.exists(logo_path):
            drawing = svg2rlg(logo_path)

            # Calculate logo dimensions (maintaining aspect ratio)
            logo_height = logo_length
            aspect_ratio = drawing.width / drawing.height
            logo_width = logo_height * aspect_ratio

            # Scale the drawing
            scale_factor = logo_height / drawing.height
            drawing.width = logo_width
            drawing.height = logo_height
            drawing.scale(scale_factor, scale_factor)

            renderPDF.draw(drawing, c, 0, 0)

    def _render_text(
        self,
        context: RendererContext,
        available_length: float,
        available_width: float
    ) -> None:
        """Render text at specified position with auto-sizing."""
        c = context.canvas

        # Build and fit text
        lines = self._build_text_lines(context)
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=available_length,
            max_height=available_width - inches_to_points(1/8),
            min_horizontal_scale=0.7,
            split_max=1,
            min_point_size=6.0
        )
        # don't add a leading offset for the last line since we have a margin
        text_content_height = calculate_total_height(fitted_lines, adjusted=True)
        margin = (available_width - text_content_height) / 2
        # Render with zero offset (already positioned at correct center)
        c.saveState()
        c.translate(0, available_width - margin)
        for fitted_line in fitted_lines:
            c.setFont(fitted_line.font_family, fitted_line.point_size)
            c.setFillColor(Color(*context.theme.effective_text_color))

            # Calculate text width with scaling
            base_width = c.stringWidth(
                fitted_line.text,
                fitted_line.font_family,
                fitted_line.point_size
            )
            scaled_width = base_width * fitted_line.horizontal_scale
            x_offset = (available_length - scaled_width) / 2
            # Draw centered text with horizontal scaling if needed
            c.translate(x_offset, -fitted_line.adjusted_point_size)
            c.scale(fitted_line.horizontal_scale, 1.0)
            c.drawString(0, 0, fitted_line.text)
            c.translate(-x_offset, -fitted_line.point_size * fitted_line.leading_ratio)
        c.restoreState()

    def _render_border(
        self,
        context: RendererContext,
        art_left_size: float,
        art_right_size: float
    ) -> None:
        """Render white border around text/logo area."""
        c = context.canvas
        border_thickness = 1.5
        border_inset = border_thickness / 2

        # Border excludes album art areas
        border_y_start = context.y + art_left_size
        border_y_end = context.y + context.height - art_right_size
        border_height = border_y_end - border_y_start

        c.setStrokeColor(Color(1.0, 1.0, 1.0))
        c.setLineWidth(border_thickness)
        c.rect(
            context.x + border_inset,
            border_y_start + border_inset,
            context.width - border_thickness,
            border_height - border_thickness,
            fill=0,
            stroke=1
        )
