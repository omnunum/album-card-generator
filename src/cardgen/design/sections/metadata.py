"""Metadata section implementation."""

from reportlab.lib.colors import Color

from cardgen.api.models import Album
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions
from cardgen.utils.genres import get_leaf_genres
from cardgen.utils.text import fit_text_adaptive


class MetadataSection(CardSection):
    """Metadata section with horizontal multi-line text in two columns."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        album: Album,
        font_size: float = 5.0,
        padding_override: float | None = None,
        min_char_spacing: float = -1.0,
    ) -> None:
        """
        Initialize metadata section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            album: Album object with genres and metadata.
            font_size: Font size in points (default: 5.0).
            padding_override: Custom padding in inches. If None, uses theme default.
            min_char_spacing: Minimum character spacing for text (negative = compressed).
        """
        super().__init__(name, dimensions)
        self.album = album
        self.font_size = font_size
        self.padding_override = padding_override
        self.min_char_spacing = min_char_spacing

    def render(self, context: RendererContext) -> None:
        """Render metadata content as two columns of vertical text (rotated 90 degrees)."""
        c = context.canvas

        # Use custom padding if provided, otherwise use theme default
        if self.padding_override is not None:
            padding = self.padding_override * 72  # Convert inches to points
        else:
            padding = context.padding

        # Process album data into left and right columns
        # Left column: Leaf genres
        leaf_genres = get_leaf_genres(self.album.genres)
        left_lines = []
        if leaf_genres:
            # First genre gets "Genre: " prefix
            left_lines.append(f"Genre: {leaf_genres[0]}")
            # Subsequent genres are indented to align with first genre
            for genre in leaf_genres[1:]:
                left_lines.append(f"            {genre}")

        # Right column: Album metadata
        right_lines = []
        if self.album.year:
            right_lines.append(f"Year: {self.album.year}")
        if self.album.label:
            right_lines.append(f"Label: {self.album.label}")
        if self.album.composer:
            right_lines.append(f"Composer: {self.album.composer}")
        right_lines.append(f"Duration: {self.album.format_total_duration()}")
        right_lines.append(f"Tracks: {len(self.album.tracks)}")

        # Calculate optimal font size to fit all lines
        # After rotation, available height for text is context.width
        # Available width is context.height (split into two halves for columns)
        available_height = context.width - (2 * padding)
        max_lines = max(len(left_lines), len(right_lines))

        # Calculate font size with 25% line spacing (same as tracklist)
        if max_lines > 0:
            calculated_font_size = available_height / (max_lines * 1.25)
            # Clamp to reasonable range
            font_size = max(5.0, min(12.0, calculated_font_size))
        else:
            font_size = self.font_size

        line_height = font_size * 1.25  # 25% line spacing

        # Set up drawing
        c.setFillColor(Color(*context.color_scheme.text))
        c.setFont(context.font_config.family, font_size)

        # Save state and set up rotation
        c.saveState()

        # Translate to bottom-left of where rotated content should appear, then rotate
        c.translate(context.x + context.width, context.y)
        c.rotate(90)  # 90 degrees counterclockwise

        # Now we're in a simple (0,0) coordinate system
        # Available space is (context.height × context.width) after rotation

        # Calculate available width for each column (half the rotated width)
        column_width = (context.height / 2) - (2 * padding)

        # Compress word spacing by 40% to fit more text (same as tracklist)
        word_spacing = -0.4 * (c.stringWidth(" ", context.font_config.family, font_size))

        # Draw left column (genres) - first half
        x_left = padding
        y_start = context.width - padding - font_size

        for i, line in enumerate(left_lines):
            y = y_start - (i * line_height)
            if y < padding:  # Check bottom boundary
                break

            # Fit text with character spacing if needed
            fit_result = fit_text_adaptive(
                c, line, column_width, context.font_config.family, font_size,
                word_spacing, self.min_char_spacing
            )
            fitted_line = fit_result['text']
            char_spacing = fit_result['char_spacing']
            c.drawString(x_left, y, fitted_line, wordSpace=word_spacing, charSpace=char_spacing)

        # Draw right column (metadata) - second half
        x_right = context.height / 2 + padding
        y_start = context.width - padding - font_size

        for i, line in enumerate(right_lines):
            y = y_start - (i * line_height)
            if y < padding:  # Check bottom boundary
                break

            # Fit text with character spacing if needed
            fit_result = fit_text_adaptive(
                c, line, column_width, context.font_config.family, font_size,
                word_spacing, self.min_char_spacing
            )
            fitted_line = fit_result['text']
            char_spacing = fit_result['char_spacing']
            c.drawString(x_right, y, fitted_line, wordSpace=word_spacing, charSpace=char_spacing)

        c.restoreState()
