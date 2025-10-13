"""PDF generation using ReportLab."""

from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from cardgen.design.base import Card, RendererContext
from cardgen.utils.dimensions import center_on_page, get_page_size, inches_to_points


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

        # Draw crop marks and fold guides if enabled
        if self.include_crop_marks:
            self._draw_guides(c, card_dims, offset_x, offset_y, card.get_fold_lines())

        # Draw each section
        sections = card.get_sections()
        for section in sections:
            self._render_section(c, section, offset_x, offset_y, card.theme)

        # Save PDF
        c.save()

    def _render_section(
        self,
        c: canvas.Canvas,
        section,  # CardSection subclass
        offset_x: float,
        offset_y: float,
        theme,
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
        dims = section.dimensions
        x = inches_to_points(offset_x + dims.x)
        y = inches_to_points(offset_y + dims.y)
        width = inches_to_points(dims.width)
        height = inches_to_points(dims.height)

        # Create rendering context
        context = RendererContext(
            canvas=c,
            x=x,
            y=y,
            width=width,
            height=height,
            font_config=theme.get_font_config(),
            color_scheme=theme.get_color_scheme(),
            padding=inches_to_points(theme.get_padding()),
            dpi=self.dpi,
        )

        # Polymorphic call - each section renders itself
        section.render(context)

    def _draw_guides(
        self,
        c: canvas.Canvas,
        card_dims: "Dimensions",  # type: ignore # noqa: F821
        offset_x: float,
        offset_y: float,
        fold_lines: list[float],
    ) -> None:
        """Draw crop marks and fold guides."""
        c.setStrokeColor(black)
        c.setLineWidth(0.5)
        c.setDash(1, 2)

        # Convert to points
        card_width = inches_to_points(card_dims.width)
        card_height = inches_to_points(card_dims.height)
        x_offset = inches_to_points(offset_x)
        y_offset = inches_to_points(offset_y)

        # Draw fold lines
        for fold_x in fold_lines:
            fold_x_pts = inches_to_points(fold_x) + x_offset
            c.line(fold_x_pts, y_offset, fold_x_pts, y_offset + card_height)

        # Draw corner crop marks
        mark_length = 18  # points
        corners = [
            (x_offset, y_offset),  # Bottom-left
            (x_offset + card_width, y_offset),  # Bottom-right
            (x_offset, y_offset + card_height),  # Top-left
            (x_offset + card_width, y_offset + card_height),  # Top-right
        ]

        c.setDash()  # Solid lines for crop marks
        for cx, cy in corners:
            # Horizontal marks
            c.line(cx - mark_length, cy, cx, cy)
            c.line(cx, cy, cx + mark_length, cy)
            # Vertical marks
            c.line(cx, cy - mark_length, cx, cy)
            c.line(cx, cy, cx, cy + mark_length)
