"""Spine section implementation."""

import os
from typing import Optional

from reportlab.graphics import renderPDF
from reportlab.lib.colors import Color
from svglib.svglib import svg2rlg

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import Dimensions, inches_to_points
from cardgen.utils.text import Line, fit_text_block


class SpineSection(CardSection):
    """Spine section with vertical text (artist, album, year) and optional album art."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        text_lines: list[str],
        album_art: Optional[AlbumArt] = None,
        show_dolby_logo: bool = False,
    ) -> None:
        """
        Initialize spine section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            text_lines: List of text strings for spine.
            album_art: Optional AlbumArt object for image processing.
            show_dolby_logo: Whether to show the Dolby NR logo on the spine.
        """
        super().__init__(name, dimensions)
        self.album_art = album_art
        self.text_items: list[str] = text_lines
        self.show_dolby_logo = show_dolby_logo

    def _build_text_lines(self, context: RendererContext) -> list[Line]:
        """
        Build Line objects for spine text.

        Args:
            context: Rendering context with font configuration.

        Returns:
            List containing a single Line object with combined spine text.
        """
        # Combine all text items with bullet separators
        combined_text = " • ".join(self.text_items)

        # Create a single line with bold font
        return [Line(
            text=combined_text,
            point_size=30,  # Start large to fill spine width, fit_text_block will reduce if needed
            leading_ratio=0.0,  # No line spacing for single line
            fixed_size=False,  # Allow size reduction
            font_family=f"{context.theme.font_family}-Bold"  # All bold
        )]

    def _render_fitted_lines(
        self,
        context: RendererContext,
        fitted_lines: list[Line],
        album_art_offset: float
    ) -> None:
        """
        Render fitted spine text with rotation.

        Args:
            context: Rendering context.
            fitted_lines: Fitted Line objects from fit_text_block.
            album_art_offset: Vertical offset to account for album art.
        """
        c = context.canvas

        # Save state for rotation
        c.saveState()

        # Translate to center of spine, offset for album art if present
        c.translate(
            context.x + context.width / 2,
            context.y + context.height / 2 + album_art_offset
        )
        c.rotate(90)  # 90 degrees counterclockwise

        # Render the single text line (centered)
        if fitted_lines:
            fitted_line = fitted_lines[0]
            c.setFont(fitted_line.font_family, fitted_line.point_size)
            c.setFillColor(Color(*context.theme.effective_text_color))

            # Calculate text width with scaling
            base_width = c.stringWidth(fitted_line.text, fitted_line.font_family, fitted_line.point_size)
            scaled_width = base_width * fitted_line.horizontal_scale

            # Draw centered text with horizontal scaling if needed
            if fitted_line.horizontal_scale < 1.0:
                c.saveState()
                c.translate(-scaled_width / 2, -fitted_line.point_size / 3)
                c.scale(fitted_line.horizontal_scale, 1.0)
                c.drawString(0, 0, fitted_line.text)
                c.restoreState()
            else:
                c.drawString(-scaled_width / 2, -fitted_line.point_size / 3, fitted_line.text)

        c.restoreState()

    def render(self, context: RendererContext) -> None:
        """Render spine with vertical text and optional album art using fit_text_block."""
        c = context.canvas

        # Calculate album art size if present
        album_art_size = inches_to_points(0.5) if self.album_art else 0
        album_art_gap = 6 if self.album_art else 0  # Small gap between art and text

        # Calculate Dolby logo size if present - half the spine height
        dolby_logo_height = (context.width / 2) if self.show_dolby_logo else 0
        dolby_logo_gap = 6 if self.show_dolby_logo else 0  # Small gap between logo and text

        # Calculate available space for text
        # Spine safe margin to prevent bleeding
        spine_safe_margin_pts = inches_to_points(0.0625)  # 1/16"

        # After rotation: height becomes length (horizontal), width becomes height (vertical)
        available_length = context.height - (2 * context.padding) - (2 * spine_safe_margin_pts) - album_art_size - album_art_gap - dolby_logo_height - dolby_logo_gap
        available_width = context.width - (2 * context.padding)

        # Render album art if present
        if self.album_art:
            art_dims = Dimensions(width=0.5, height=0.5, dpi=context.dpi)
            point_dims = art_dims.to_points()
            pixel_dims = art_dims.to_pixels()

            processed_img = self.album_art.resize_and_crop((pixel_dims.width, pixel_dims.height), mode="square")

            c.saveState()
            art_center_x = context.x + context.width / 2
            art_center_y = context.y + context.height - (point_dims.height / 2)
            c.translate(art_center_x, art_center_y)
            c.rotate(90)

            img_reader = self.album_art.to_image_reader(processed_img)
            c.drawImage(img_reader, -point_dims.width / 2, -point_dims.height / 2, width=point_dims.width, height=point_dims.height, preserveAspectRatio=True)
            c.restoreState()

        # Render Dolby logo if requested
        if self.show_dolby_logo:
            # Load the white Dolby logo SVG
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets')
            logo_path = os.path.join(assets_dir, 'dolby-b-logo-white.svg')

            if os.path.exists(logo_path):
                drawing = svg2rlg(logo_path)

                # Calculate logo dimensions (half the spine height, maintaining aspect ratio)
                logo_height = dolby_logo_height
                aspect_ratio = drawing.width / drawing.height
                logo_width = logo_height * aspect_ratio

                # Scale the drawing
                scale_factor = logo_height / drawing.height
                drawing.width = logo_width
                drawing.height = logo_height
                drawing.scale(scale_factor, scale_factor)

                c.saveState()
                # Position logo to the left of text (after album art if present)
                logo_center_x = context.x + context.width / 2
                logo_y_offset = context.height - album_art_size - album_art_gap - (dolby_logo_height / 2)
                logo_center_y = context.y + logo_y_offset

                c.translate(logo_center_x, logo_center_y)
                c.rotate(90)

                # Center the logo
                renderPDF.draw(drawing, c, -logo_width / 2, -logo_height / 2)
                c.restoreState()

        # Draw white border around text/logo area (non-album-art section)
        # Border extends to album art edge (gap is only for text/logo positioning)
        border_thickness = 1.5
        border_y_start = context.y
        border_y_end = context.y + context.height - album_art_size  # No gap subtraction
        border_height = border_y_end - border_y_start

        # Inset by half border thickness so entire border is inside
        border_inset = border_thickness / 2

        c.setStrokeColor(Color(1.0, 1.0, 1.0))  # White border
        c.setLineWidth(border_thickness)
        c.rect(
            context.x + border_inset,
            border_y_start + border_inset,
            context.width - border_thickness,
            border_height - border_thickness,
            fill=0,
            stroke=1
        )

        # Build text lines
        lines = self._build_text_lines(context)

        # Fit text to available space
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=available_length,  # Length constraint (horizontal after rotation)
            max_height=available_width,  # Width constraint (vertical after rotation)
            min_horizontal_scale=0.7,
            split_max=1,  # Allow splitting to 2 lines if needed
            min_point_size=6.0
        )

        # Calculate text center offset for album art and Dolby logo
        text_center_offset = 0
        if self.album_art or self.show_dolby_logo:
            total_offset = album_art_size + album_art_gap + dolby_logo_height + dolby_logo_gap
            text_center_offset = -total_offset / 2

        # Render fitted text
        self._render_fitted_lines(context, fitted_lines, text_center_offset)
