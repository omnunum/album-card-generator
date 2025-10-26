"""Spine section implementation."""

from dataclasses import dataclass
from typing import Optional

from reportlab.lib.colors import Color

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import Dimensions, SAFE_MARGIN, inches_to_points
from cardgen.utils.text import calculate_optimal_char_spacing, calculate_text_width


@dataclass
class SpineTextItem:
    """A text item for the spine with optional bold styling."""
    text: str
    bold: bool = False


class SpineSection(CardSection):
    """Spine section with vertical text (artist, album, year) and optional album art."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        text_lines: list[str] | list[SpineTextItem],
        album_art: Optional[AlbumArt] = None,
    ) -> None:
        """
        Initialize spine section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            text_lines: List of text lines (strings or SpineTextItem objects).
            album_art: Optional AlbumArt object for image processing.
        """
        super().__init__(name, dimensions)
        self.album_art = album_art
        # Convert strings to SpineTextItem if needed
        self.text_items: list[SpineTextItem] = []
        for item in text_lines:
            if isinstance(item, str):
                self.text_items.append(SpineTextItem(text=item))
            else:
                self.text_items.append(item)

    def render(self, context: RendererContext) -> None:
        """Render spine with vertical text and optional album art, sized to fit available space."""
        c = context.canvas

        c.setFillColor(Color(*context.color_scheme.text))

        # Calculate album art size if present (0.5" x 0.5" square, full bleed)
        album_art_size = inches_to_points(0.5) if self.album_art else 0
        album_art_gap = 6 if self.album_art else 0  # Small gap between art and text

        # Calculate the largest font size that will fit
        # Available length is the height (since text is rotated 90 degrees)
        available_length = context.height - (context.padding * 2)
        available_width = context.width - (context.padding * 2)

        # Apply safe margin to prevent text bleeding into adjacent panels
        # Reduced safe margin for spine - only need small buffer
        spine_safe_margin = 0.0625  # 1/16" = 4.5pt (half of standard SAFE_MARGIN)
        safe_margin_pts = inches_to_points(spine_safe_margin)
        effective_available_length = available_length - (safe_margin_pts * 2) - album_art_size - album_art_gap

        # Combine text to calculate width (using bold where needed)
        combined_text = " • ".join([item.text for item in self.text_items])

        # Strategy: Start with maximum font size that fills the spine width (text height),
        # then compress character spacing if needed. Only reduce font size when we hit
        # minimum character spacing threshold AND text still doesn't fit.

        # Start with font size that fills the available width (height constraint for rotated spine text)
        font_size = available_width  # Max 36pt for 0.5" spine (full width)
        min_font_size = 6
        min_char_spacing = -0.3  # Minimum kerning before we reduce font size (prevent overlap)
        char_spacing = 0.0

        # Find optimal font size by iterating down from maximum
        while font_size >= min_font_size:
            # Measure text length at this font size (normal spacing)
            text_length = c.stringWidth(combined_text, context.font_config.family, font_size)

            # Check if text fits with normal spacing
            if text_length <= effective_available_length:
                # Perfect! Use this size with normal spacing
                char_spacing = 0.0
                break

            # Text too long - try compressing character spacing first
            char_spacing = calculate_optimal_char_spacing(
                c, combined_text, context.font_config.family, font_size,
                effective_available_length, min_spacing=min_char_spacing
            )

            # Calculate word spacing (proportionally more compression for spaces)
            word_spacing = char_spacing * 3

            # Calculate compressed text length (accounting for both char and word spacing)
            compressed_length = calculate_text_width(
                c, combined_text, context.font_config.family, font_size, char_spacing, word_spacing
            )

            # Check if compressed text now fits
            if compressed_length <= effective_available_length:
                # Found it! Use this font size with compressed spacing
                break

            # Even with max compression doesn't fit - reduce font size and try again
            font_size -= 0.5

        # Ensure we don't go below minimum font size
        font_size = max(font_size, min_font_size)

        # Check if we should switch to two-line mode
        # If font size is very small (< 10pt) and we have at least 2 items, try two-line layout
        use_two_line_mode = False
        artist_line_char_spacing = 0.0
        remaining_line_char_spacing = 0.0

        import sys
        print(f"DEBUG SPINE: font_size={font_size:.1f}pt, items={len(self.text_items)}, text='{combined_text[:50]}'", file=sys.stderr)

        if font_size < 10 and len(self.text_items) >= 2:
            # Calculate if two lines would allow bigger font
            # Two lines: each gets half the width
            two_line_font_size = available_width / 2  # Each line gets half the width

            # Check if first item (artist) fits on one line at this size (with compression if needed)
            artist_text = self.text_items[0].text
            artist_width = c.stringWidth(artist_text, context.font_config.family, two_line_font_size)

            # Check if remaining items fit on second line (with compression if needed)
            remaining_text = " • ".join([item.text for item in self.text_items[1:]])
            remaining_width = c.stringWidth(remaining_text, context.font_config.family, two_line_font_size)

            print(f"DEBUG TWO-LINE CHECK: two_line_font={two_line_font_size:.1f}pt, artist_width={artist_width:.1f}, remaining_width={remaining_width:.1f}, available_length={effective_available_length:.1f}", file=sys.stderr)

            # Calculate compression needed for each line
            artist_char_spacing = 0.0
            remaining_char_spacing = 0.0

            if artist_width > effective_available_length:
                artist_char_spacing = calculate_optimal_char_spacing(
                    c, artist_text, context.font_config.family, two_line_font_size,
                    effective_available_length, min_spacing=min_char_spacing
                )
                artist_word_spacing = artist_char_spacing * 3
                artist_compressed = calculate_text_width(
                    c, artist_text, context.font_config.family, two_line_font_size,
                    artist_char_spacing, artist_word_spacing
                )
            else:
                artist_compressed = artist_width

            if remaining_width > effective_available_length:
                remaining_char_spacing = calculate_optimal_char_spacing(
                    c, remaining_text, context.font_config.family, two_line_font_size,
                    effective_available_length, min_spacing=min_char_spacing
                )
                remaining_word_spacing = remaining_char_spacing * 3
                remaining_compressed = calculate_text_width(
                    c, remaining_text, context.font_config.family, two_line_font_size,
                    remaining_char_spacing, remaining_word_spacing
                )
            else:
                remaining_compressed = remaining_width

            print(f"DEBUG COMPRESSION: artist_compressed={artist_compressed:.1f}, remaining_compressed={remaining_compressed:.1f}", file=sys.stderr)

            # If both lines fit with compression OR if two-line mode gives us bigger font than single line
            if (artist_compressed <= effective_available_length and remaining_compressed <= effective_available_length) or two_line_font_size > font_size:
                use_two_line_mode = True
                font_size = two_line_font_size
                # Store per-line char spacing
                artist_line_char_spacing = artist_char_spacing
                remaining_line_char_spacing = remaining_char_spacing
                # For single-line fallback compatibility, use the worst spacing
                char_spacing = min(artist_char_spacing, remaining_char_spacing)
                print(f"DEBUG: SWITCHING TO TWO-LINE MODE! artist_spacing={artist_line_char_spacing:.2f}, remaining_spacing={remaining_line_char_spacing:.2f}", file=sys.stderr)

        # Render album art if present (rotated 90 degrees to align with spine text)
        if self.album_art:
            # Album art: 0.5" x 0.5" square at top of spine (full bleed)
            art_size = inches_to_points(0.5)

            # Resize and crop album art to square
            target_px = int((art_size / 72) * context.dpi)
            processed_img = self.album_art.resize_and_crop((target_px, target_px), mode="square")

            # Save state for rotation
            c.saveState()

            # Calculate center point of where the album art will be
            # Position at top of spine
            art_center_x = context.x + context.width / 2
            art_center_y = context.y + context.height - (art_size / 2)

            # Translate to center point, rotate 90 degrees, then draw
            c.translate(art_center_x, art_center_y)
            c.rotate(90)

            # Convert PIL image to ImageReader
            img_reader = self.album_art.to_image_reader(processed_img)

            # Draw image centered at origin (which is now the rotated center point)
            c.drawImage(
                img_reader,
                -art_size / 2,
                -art_size / 2,
                width=art_size,
                height=art_size,
                preserveAspectRatio=True,
            )

            # Restore state after drawing rotated image
            c.restoreState()

        # Save state, rotate, and draw vertical text
        c.saveState()

        # Rotate 90 degrees counterclockwise and position text
        # If we have album art, we need to shift the text center down to account for it
        # The text should be centered in the remaining space (after album art + gap)
        text_center_offset = 0
        if self.album_art:
            # Offset = half of (album_art_size + gap) to shift center point down
            text_center_offset = -(album_art_size + album_art_gap) / 2

        c.translate(
            context.x + context.width / 2,
            context.y + context.height / 2 + text_center_offset
        )
        c.rotate(90)

        # Calculate word spacing - need to compress spaces proportionally to char_spacing
        word_spacing = char_spacing * 3  # Spaces need ~3x compression to match char compression

        if use_two_line_mode:
            # Two-line layout: Artist on top line, Title • Year on bottom line
            line_gap = 2  # Gap between the two lines

            # Line 1: Artist (top) - use artist-specific spacing
            artist_item = self.text_items[0]
            artist_font = f"{context.font_config.family}-Bold" if artist_item.bold else context.font_config.family
            artist_word_spacing = artist_line_char_spacing * 3
            artist_width = calculate_text_width(
                c, artist_item.text, artist_font, font_size,
                artist_line_char_spacing, artist_word_spacing
            )

            # Line 2: Remaining items (bottom) - use remaining-specific spacing
            remaining_items = self.text_items[1:]
            remaining_parts = []
            remaining_total_width = 0
            remaining_word_spacing = remaining_line_char_spacing * 3

            for i, item in enumerate(remaining_items):
                font_name = f"{context.font_config.family}-Bold" if item.bold else context.font_config.family
                text = item.text
                if i > 0:
                    sep = " • "
                    sep_width = calculate_text_width(
                        c, sep, context.font_config.family, font_size,
                        remaining_line_char_spacing, remaining_word_spacing
                    )
                    remaining_parts.append((sep, context.font_config.family, sep_width, True))
                    remaining_total_width += sep_width

                text_width = calculate_text_width(
                    c, text, font_name, font_size,
                    remaining_line_char_spacing, remaining_word_spacing
                )
                remaining_parts.append((text, font_name, text_width, False))
                remaining_total_width += text_width

            # Draw Line 1 (artist) - top half
            c.setFont(artist_font, font_size)
            line1_y = font_size / 2 + line_gap / 2
            c.drawString(-artist_width / 2, line1_y - font_size / 3, artist_item.text,
                        charSpace=artist_line_char_spacing, wordSpace=artist_word_spacing)

            # Draw Line 2 (title + year) - bottom half
            line2_y = -font_size / 2 - line_gap / 2
            current_x = -remaining_total_width / 2
            for text, font_name, text_width, is_sep in remaining_parts:
                c.setFont(font_name, font_size)
                c.drawString(current_x, line2_y - font_size / 3, text,
                            charSpace=remaining_line_char_spacing, wordSpace=remaining_word_spacing)
                current_x += text_width
        else:
            # Single-line layout (original)
            # Calculate total width for centering (accounting for character and word spacing)
            total_width = 0
            current_x = 0
            widths = []

            for i, item in enumerate(self.text_items):
                font_name = f"{context.font_config.family}-Bold" if item.bold else context.font_config.family
                text = item.text
                if i > 0:
                    # Add separator
                    sep = " • "
                    sep_width = calculate_text_width(
                        c, sep, context.font_config.family, font_size,
                        char_spacing, word_spacing
                    )
                    total_width += sep_width
                text_width = calculate_text_width(
                    c, text, font_name, font_size,
                    char_spacing, word_spacing
                )
                widths.append((text, font_name, text_width, i > 0))
                total_width += text_width

            # Draw each segment
            current_x = -total_width / 2
            for text, font_name, text_width, has_separator in widths:
                if has_separator:
                    # Draw separator
                    c.setFont(context.font_config.family, font_size)
                    sep = " • "
                    c.drawString(current_x, -font_size / 3, sep, charSpace=char_spacing, wordSpace=word_spacing)
                    sep_width = calculate_text_width(
                        c, sep, context.font_config.family, font_size,
                        char_spacing, word_spacing
                    )
                    current_x += sep_width

                # Draw text
                c.setFont(font_name, font_size)
                c.drawString(current_x, -font_size / 3, text, charSpace=char_spacing, wordSpace=word_spacing)
                current_x += text_width

        c.restoreState()
