"""PDF generation using ReportLab."""

from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import gray, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from cardgen.config import Theme
from cardgen.design.base import Card, CardSection, RendererContext
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import (
    Dimensions,
    PixelDims,
    PointDims,
    center_on_page,
    get_page_size,
    inches_to_points,
)


class PDFRenderer:
    """Renders cards to PDF using ReportLab."""

    def __init__(self, dpi: int = 600, include_crop_marks: bool = True, page_size: str = "letter") -> None:
        """
        Initialize PDF renderer.

        Args:
            dpi: DPI for image rendering.
            include_crop_marks: Whether to include crop marks and fold guides.
            page_size: Page size name (e.g., "letter", "half", "a4", "a5").
        """
        self.dpi = dpi
        self.include_crop_marks = include_crop_marks

        # Get page size from registry
        ps = get_page_size(page_size)
        self.page_width = ps.width
        self.page_height = ps.height

    def render_card(self, card: Card, output_path: Path) -> None:
        """
        Render card to PDF file.

        Args:
            card: Card object to render.
            output_path: Path to output PDF file.
        """
        # Create canvas with specified page size
        page_size_pts = (inches_to_points(self.page_width), inches_to_points(self.page_height))
        c = canvas.Canvas(str(output_path), pagesize=page_size_pts)

        # Get card dimensions
        card_dims = card.get_dimensions()

        # Center card on page
        offset_x, offset_y = center_on_page(card_dims.width, card_dims.height, self.page_width, self.page_height)

        # Draw each section
        sections = card.get_sections()
        for section in sections:
            self._render_section(c, section, offset_x, offset_y, card.theme)

        # Draw color palette legend if available
        if card.theme.color_palette:
            self._draw_color_palette(c, card.theme.color_palette, card_dims, offset_x, offset_y)

        # Draw crop marks and fold guides on top of everything
        if self.include_crop_marks:
            self._draw_guides(c, card_dims, offset_x, offset_y, card.get_fold_lines())

        # Save PDF
        c.save()

    def render_cards(self, cards: list[Card], output_path: Path) -> None:
        """
        Render multiple cards to PDF file, stacked vertically (2 per page).

        Cards are aligned to the top of each half-page slot, not centered.

        Args:
            cards: List of Card objects to render.
            output_path: Path to output PDF file.
        """
        # Create canvas with specified page size (landscape for horizontal layout)
        page_size_pts = (inches_to_points(self.page_height), inches_to_points(self.page_width))
        c = canvas.Canvas(str(output_path), pagesize=page_size_pts)

        # Process cards 2 at a time (one page)
        for page_idx in range(0, len(cards), 2):
            cards_on_page = cards[page_idx:page_idx + 2]

            # Half page height for vertical stacking
            half_page_height = self.page_width / 2  # page is rotated

            for slot_idx, card in enumerate(cards_on_page):
                card_dims = card.get_dimensions()

                # Center horizontally, align to top of slot
                offset_x = (self.page_height - card_dims.width) / 2
                # Top slot (slot 0) or bottom slot (slot 1)
                slot_y = self.page_width - (slot_idx + 1) * half_page_height
                # Align to top of slot with small margin
                offset_y = slot_y + half_page_height - card_dims.height - 0.125  # 0.125" top margin

                # Draw gradient background if enabled
                if card.theme.use_gradient and card.theme.gradient_start and card.theme.gradient_end:
                    # Add 1/16" bleed on all sides to prevent white edges when cutting
                    bleed = 0.0625  # 1/16"
                    gradient_dims = Dimensions(
                        width=card_dims.width + (2 * bleed),  # Extend left and right
                        height=card_dims.height + (2 * bleed),  # Extend top and bottom
                        x=offset_x - bleed,  # Shift left to center the extension
                        y=offset_y - bleed,  # Shift down to center the extension
                        dpi=self.dpi
                    )
                    self._draw_gradient_background(
                        c, gradient_dims, card.theme.gradient_start, card.theme.gradient_end
                    )

                # Draw each section
                sections = card.get_sections()
                for section in sections:
                    self._render_section(c, section, offset_x, offset_y, card.theme)

                # Draw color palette legend if available
                if card.theme.color_palette:
                    self._draw_color_palette(c, card.theme.color_palette, card_dims, offset_x, offset_y)

                # Draw crop marks and fold guides on top of everything
                if self.include_crop_marks:
                    self._draw_guides(c, card_dims, offset_x, offset_y, card.get_fold_lines())

            # Start new page if there are more cards
            if page_idx + 2 < len(cards):
                c.showPage()

        # Save PDF
        c.save()

    def _render_section(
        self,
        c: canvas.Canvas,
        section: CardSection,  # CardSection subclass
        offset_x: float,
        offset_y: float,
        theme: Theme,
    ) -> None:
        """
        Render a single card section using polymorphism.

        Args:
            c: ReportLab canvas.
            section: CardSection subclass to render.
            offset_x: X offset for card position on page (inches).
            offset_y: Y offset for card position on page (inches).
            theme: Theme for styling.
        """
        # Create positioned section dimensions
        positioned_dims = Dimensions(
            width=section.dimensions.width,
            height=section.dimensions.height,
            x=offset_x + section.dimensions.x,
            y=offset_y + section.dimensions.y,
            dpi=self.dpi
        )
        point_dims = positioned_dims.to_points()

        # Create rendering context
        context = RendererContext(
            canvas=c,
            x=point_dims.x,
            y=point_dims.y,
            width=point_dims.width,
            height=point_dims.height,
            theme=theme,
            padding=inches_to_points(theme.padding),
            dpi=self.dpi,
        )

        # Polymorphic call - each section renders itself
        section.render(context)

    def _draw_gradient_background(
        self,
        c: canvas.Canvas,
        dims: Dimensions,
        start_color: tuple[float, float, float],
        end_color: tuple[float, float, float],
    ) -> None:
        """
        Draw a vertical gradient background using a PIL-generated image.

        Args:
            c: ReportLab canvas.
            dims: Dimensions in inches (will be converted to pixels/points).
            start_color: RGB tuple (0-1) for top of gradient.
            end_color: RGB tuple (0-1) for bottom of gradient.
        """
        # Get pixel dimensions for image generation
        pixel_dims = dims.to_pixels()
        img_width = pixel_dims.width
        img_height = pixel_dims.height

        # Create new image
        img = PILImage.new('RGB', (img_width, img_height))
        pixels = img.load()

        # Convert colors from 0-1 to 0-255
        start_r = int(start_color[0] * 255)
        start_g = int(start_color[1] * 255)
        start_b = int(start_color[2] * 255)

        end_r = int(end_color[0] * 255)
        end_g = int(end_color[1] * 255)
        end_b = int(end_color[2] * 255)

        # Generate gradient pixel by pixel
        for py in range(img_height):
            # Calculate interpolation factor (0 to 1 from top to bottom)
            t = py / img_height

            # Use softened cubic interpolation (80% cubic, 20% linear) for more color at edges, less in middle
            t_cubic = 0.8 * (3 * t**2 - 2 * t**3) + 0.2 * t

            # Interpolate colors
            r = int(start_r + t_cubic * (end_r - start_r))
            g = int(start_g + t_cubic * (end_g - start_g))
            b = int(start_b + t_cubic * (end_b - start_b))

            # Fill entire row with this color
            for px in range(img_width):
                pixels[px, py] = (r, g, b)

        # Convert PIL image to ImageReader
        img_reader = AlbumArt.pil_to_image_reader(img)

        # Get point dimensions for PDF drawing
        point_dims = dims.to_points()
        c.drawImage(
            img_reader,
            point_dims.x, point_dims.y,
            width=point_dims.width,
            height=point_dims.height,
            preserveAspectRatio=False
        )

    def _draw_color_palette(
        self,
        c: canvas.Canvas,
        palette: list[tuple[float, float, float]],
        card_dims: "Dimensions",  # type: ignore # noqa: F821
        offset_x: float,
        offset_y: float,
    ) -> None:
        """Draw color palette legend outside the card area."""
        from reportlab.lib.colors import Color, black

        # Create positioned card dimensions
        positioned_card = Dimensions(
            width=card_dims.width,
            height=card_dims.height,
            x=offset_x,
            y=offset_y
        )
        point_dims = positioned_card.to_points()

        # Position palette to the right of the card
        palette_x = point_dims.x + point_dims.width + 18  # 18pts gap from card
        palette_y_start = point_dims.y + point_dims.height - 16  # Start slightly lower

        swatch_width = 24  # 24pts width (unchanged for surface area)
        swatch_height = 16  # 16pts height (reduced from 24 for density)
        gap = 1  # 2pts gap between swatches (reduced from 4)
        font_size = 6  # 6pts font (reduced from 7)

        c.setFont("Helvetica", font_size)

        for i, color in enumerate(palette):
            # Calculate position - 26pts vertical spacing per swatch
            y = palette_y_start - i * (swatch_height + gap + font_size + 2)

            # Draw colored rectangle
            r, g, b = color
            c.setFillColor(Color(r, g, b))
            c.setStrokeColor(black)
            c.setLineWidth(0.5)
            c.rect(palette_x, y, swatch_width, swatch_height, fill=1, stroke=1)

            # Draw number label
            c.setFillColor(black)
            c.drawString(palette_x, y + swatch_height + 2, f"{i}")

            # Draw hex color code
            hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            c.drawString(palette_x + swatch_width + 4, y + swatch_height / 2 - 2, hex_color)

    def _draw_guides(
        self,
        c: canvas.Canvas,
        card_dims: "Dimensions",  # type: ignore # noqa: F821
        offset_x: float,
        offset_y: float,
        fold_lines: list[float],
    ) -> None:
        """Draw crop marks and fold guides."""
        # Create positioned card dimensions
        positioned_card = Dimensions(
            width=card_dims.width,
            height=card_dims.height,
            x=offset_x,
            y=offset_y
        )
        point_dims = positioned_card.to_points()

        # Draw fold lines (white, sparsely dotted)
        c.setStrokeColor(white)
        c.setLineWidth(0.25)
        c.setDash(1, 2)  # More sparse dotted pattern

        for fold_x in fold_lines:
            fold_x_pts = inches_to_points(fold_x) + point_dims.x
            c.line(fold_x_pts, point_dims.y, fold_x_pts, point_dims.y + point_dims.height)

        # Draw corner crop marks (gray, solid)
        c.setStrokeColor(gray)
        c.setDash()  # Solid lines for crop marks
        mark_length = 9  # points (half size to prevent bleeding into neighboring cards)

        corners = [
            (point_dims.x, point_dims.y),  # Bottom-left
            (point_dims.x + point_dims.width, point_dims.y),  # Bottom-right
            (point_dims.x, point_dims.y + point_dims.height),  # Top-left
            (point_dims.x + point_dims.width, point_dims.y + point_dims.height),  # Top-right
        ]

        for cx, cy in corners:
            # Horizontal marks
            c.line(cx - mark_length, cy, cx, cy)
            c.line(cx, cy, cx + mark_length, cy)
            # Vertical marks
            c.line(cx, cy - mark_length, cx, cy)
            c.line(cx, cy, cx, cy + mark_length)
