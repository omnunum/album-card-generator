"""Tracklist section implementation."""

from dataclasses import dataclass
from typing import Optional

from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen.canvas import Canvas

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions
from cardgen.utils.tape import TapeSide


@dataclass
class MinimapSegment:
    """A segment in the minimap (track or empty space)."""
    duration: float  # Duration in seconds
    track_number: Optional[int] = None  # None for empty space
    is_hatched: bool = False  # True for empty/unused space


class TracklistSection(CardSection):
    """Tracklist section with Side A/B and duration minimap."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        side_a: TapeSide,
        side_b: TapeSide,
        title: str = "Tracklist",
        track_title_overflow: str = "truncate",
        min_char_spacing: float = -1.0,
    ) -> None:
        """
        Initialize tracklist section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            side_a: Tape Side A with tracks.
            side_b: Tape Side B with tracks.
            title: Section title.
            track_title_overflow: How to handle long track titles ("truncate" or "wrap").
            min_char_spacing: Minimum character spacing for track titles (negative = compressed).
        """
        super().__init__(name, dimensions)
        self.side_a = side_a
        self.side_b = side_b
        self.title = title
        self.track_title_overflow = track_title_overflow
        self.min_char_spacing = min_char_spacing

    def render(self, context: RendererContext) -> None:
        """Render track listing with Side A/B and duration minimap."""
        c = context.canvas

        # Horizontal minimap bar height (under each side label)
        minimap_height = 10  # points
        minimap_gap = 4  # gap between minimap and tracks

        c.setFillColor(Color(*context.color_scheme.text))

        # Title
        c.setFont(
            f"{context.font_config.family}-Bold", context.font_config.title_size
        )
        text_y = context.y + context.height - context.padding - context.font_config.title_size
        c.drawString(context.x + context.padding, text_y, self.title)

        # Calculate optimal font size that fits with proportional line spacing (25% of font size)
        available_height = text_y - context.font_config.title_size - 10 - context.y - context.padding

        side_a_track_count = len(self.side_a.tracks if self.side_a else [])
        side_b_track_count = len(self.side_b.tracks if self.side_b else [])
        total_tracks = side_a_track_count + side_b_track_count

        num_headers = 2 if (self.side_a and self.side_b) else 1
        total_lines = total_tracks + num_headers + 1  # tracks + headers + gap between sides

        # Find largest font size that fits with 25% line spacing
        # available = total_lines * (font_size + 0.25 * font_size) = total_lines * 1.25 * font_size
        track_size = available_height / (total_lines * 1.25)
        # Clamp to reasonable range
        track_size = max(8.0, min(12.0, track_size))
        line_spacing = track_size * 0.25

        c.setFont(context.font_config.family, track_size)
        text_y -= track_size + 10

        # Available width for track text (full width now that minimap is horizontal)
        text_width = context.width - (context.padding * 2)

        # Minimap width spans full text width
        minimap_width = text_width
        minimap_x = context.x + context.padding

        # Calculate Side A unused space for Side B offset
        side_a_unused_duration = 0
        if self.side_a and self.side_a.tracks:
            total_side_a_duration = sum(track.duration for track in self.side_a.tracks)
            side_a_unused_duration = self.side_a.max_duration - total_side_a_duration

        # Render Side A
        if self.side_a and self.side_a.tracks:
            text_y = self._render_tape_side(
                context, self.side_a, "Side A", text_y, text_width,
                minimap_x, text_y, minimap_width, minimap_height,
                unused_duration_offset=0, track_size=track_size, line_spacing=line_spacing,
                minimap_gap=minimap_gap
            )
            text_y -= line_spacing  # Gap between sides

        # Render Side B
        if self.side_b and self.side_b.tracks:
            # Always render Side B - we calculated space for it
            text_y = self._render_tape_side(
                context, self.side_b, "Side B", text_y, text_width,
                minimap_x, text_y, minimap_width, minimap_height,
                unused_duration_offset=side_a_unused_duration, track_size=track_size, line_spacing=line_spacing,
                minimap_gap=minimap_gap
            )

    def _render_tape_side(
        self,
        context: RendererContext,
        tape_side: TapeSide,
        label: str,
        text_y: float,
        text_width: float,
        minimap_x: float,
        minimap_y: float,
        minimap_width: float,
        minimap_height: float,
        unused_duration_offset: float = 0,
        track_size: float = 10,
        line_spacing: float = 3,
        minimap_gap: float = 4,
    ) -> float:
        """
        Render a single tape side (A or B) with tracks and horizontal minimap.

        Args:
            context: Rendering context.
            tape_side: Tape side to render.
            label: Label to display ("Side A" or "Side B").
            text_y: Current y position for text.
            text_width: Available width for track text.
            minimap_x: Unused (kept for compatibility).
            minimap_y: Unused (kept for compatibility).
            minimap_width: Unused (kept for compatibility).
            minimap_height: Height of minimap bar.
            unused_duration_offset: Duration offset for Side B tape flip logic.
            track_size: Font size for tracks.
            line_spacing: Line spacing between tracks.
            minimap_gap: Unused (minimap is inline with label).

        Returns:
            Updated text_y position after rendering.
        """
        c = context.canvas

        # Ensure text color is set (fixes white text bug for Side B)
        c.setFillColor(Color(*context.color_scheme.text))

        # Side header
        c.setFont(f"{context.font_config.family}-Bold", track_size)
        c.drawString(context.x + context.padding, text_y, label)

        # Draw horizontal minimap to the right of the side label (on the same line)
        # Position minimap starting after the label text
        label_width = c.stringWidth(label, f"{context.font_config.family}-Bold", track_size)
        minimap_left_margin = 12  # Gap between label and minimap
        minimap_start_x = context.x + context.padding + label_width + minimap_left_margin
        minimap_available_width = text_width - label_width - minimap_left_margin

        # Align minimap centerline with label text centerline
        # Text baseline is at text_y, text height is track_size
        # Text center is approximately at: text_y + track_size / 2 (accounting for descenders)
        # For better visual alignment, use text_y + track_size * 0.35 as the centerline
        text_centerline = text_y + track_size * 0.35
        # Minimap center should align with text center
        # minimap_top_y - minimap_height/2 = text_centerline
        minimap_top_y = text_centerline + minimap_height / 2

        self._draw_minimap(
            context,
            tape_side,
            minimap_start_x,
            minimap_top_y,
            minimap_available_width,
            minimap_height,
            unused_duration_offset,
        )

        text_y -= track_size + line_spacing

        # Move down after the side header (no extra space needed for minimap since it's inline)
        # text_y is already positioned for next line

        # Ensure text color is reset after minimap drawing
        c.setFillColor(Color(*context.color_scheme.text))

        # Side tracks
        # Compress word spacing by 40% to fit more text
        word_spacing = -0.4 * (c.stringWidth(" ", context.font_config.family, track_size))

        for track in tape_side.tracks:
            # Format track number as right-aligned (e.g., ' 9' or '10')
            # Split into number+period (monospace) and space (Helvetica for narrower spacing)
            track_num_text = f"{track.track_number:2d}."
            track_title_text = track.title
            duration_text = track.format_duration()

            # Calculate duration width (using monospace font)
            duration_width = c.stringWidth(
                duration_text,
                context.font_config.monospace_family,
                track_size,
            )
            # No word spacing needed for duration (monospace, no spaces)
            duration_x = context.x + context.padding + text_width - duration_width

            # Calculate available width for track text (leave gap before duration)
            gap_before_duration = 3  # points - small gap between title and duration
            available_track_width = duration_x - (context.x + context.padding) - gap_before_duration

            # Calculate widths for track number (monospace) + Helvetica space
            track_num_width = c.stringWidth(track_num_text, context.font_config.monospace_family, track_size)
            helvetica_space_width = c.stringWidth(" ", context.font_config.family, track_size)
            total_track_num_width = track_num_width + helvetica_space_width

            # Calculate available widths for line 1 and line 2
            line1_available_width = available_track_width - total_track_num_width
            # Line 2: 4 monospace spaces (indent) to right padding
            indent_width = c.stringWidth("    ", context.font_config.monospace_family, track_size)
            line2_available_width = text_width - indent_width

            # Use adaptive fitting algorithm
            line1_text, line2_text, char_spacing, line2_char_spacing = self._fit_track_title_adaptive(
                c, track_title_text,
                line1_available_width, line2_available_width,
                context.font_config.family, track_size, word_spacing, self.min_char_spacing
            )

            # Draw track number in monospace (without space)
            c.setFont(context.font_config.monospace_family, track_size)
            c.drawString(context.x + context.padding, text_y, track_num_text)

            # Draw Helvetica space after track number
            c.setFont(context.font_config.family, track_size)
            c.drawString(context.x + context.padding + track_num_width, text_y, " ")

            # Draw first line with character spacing (after the Helvetica space)
            c.drawString(
                context.x + context.padding + total_track_num_width, text_y, line1_text,
                wordSpace=word_spacing, charSpace=char_spacing
            )

            # Draw duration in monospace font (only on first line)
            c.setFont(context.font_config.monospace_family, track_size)
            c.drawString(duration_x, text_y, duration_text)

            # Draw second line if it exists
            if line2_text:
                text_y -= track_size + line_spacing

                # Draw 4 monospace spaces for indent
                monospace_indent = "    "
                c.setFont(context.font_config.monospace_family, track_size)
                c.drawString(context.x + context.padding, text_y, monospace_indent)

                # Draw line 2 text after the monospace indent
                c.setFont(context.font_config.family, track_size)
                c.drawString(
                    context.x + context.padding + indent_width, text_y, line2_text,
                    wordSpace=word_spacing, charSpace=line2_char_spacing
                )

            text_y -= track_size + line_spacing

        return text_y

    def _calculate_optimal_line_size(
        self, available_height: float, total_lines: int
    ) -> tuple[float, float]:
        """
        Calculate optimal font size and line spacing to fill available vertical space.

        Args:
            available_height: Available vertical space.
            total_lines: Total number of lines (tracks + headers).

        Returns:
            Tuple of (font_size, line_spacing).
        """
        min_size = 6
        max_size = 12

        # Try each font size from largest to smallest
        for size in range(int(max_size), int(min_size) - 1, -1):
            # Calculate spacing needed to fill the space
            # available = total_lines * (size + spacing)
            spacing = (available_height / total_lines) - size

            # Spacing should be reasonable (at least 2pt, at most 10pt)
            if spacing >= 2 and spacing <= 10:
                return (float(size), spacing)

        # Fallback: use minimum size with whatever spacing fits
        spacing = max(2.0, (available_height / total_lines) - min_size)
        return (float(min_size), spacing)

    def _calculate_track_font_size(
        self, available_height: float, total_tracks: int, num_headers: int, overhead: float
    ) -> float:
        """
        Calculate optimal track font size to fit all tracks in available space.

        Args:
            available_height: Available vertical space for tracks.
            total_tracks: Total number of tracks across both sides.
            num_headers: Number of side headers (1 or 2).
            overhead: Fixed overhead from spacing and headers.

        Returns:
            Optimal font size in points.
        """
        min_size = 6
        max_size = 12

        # Formula: height = tracks*(size+3) + headers*(size+4) + gap_between_sides
        # Each track uses: size + 3pt spacing
        # Each header uses: size + 4pt spacing
        for size in range(int(max_size), int(min_size) - 1, -1):
            track_space = total_tracks * (size + 3)
            header_space = num_headers * (size + 4)
            required_height = track_space + header_space + overhead

            if required_height <= available_height:
                return float(size)

        return float(min_size)

    def _build_minimap_segments(
        self, tape_side: TapeSide, unused_duration_offset: float = 0
    ) -> list[MinimapSegment]:
        """Build list of segments for minimap rendering."""
        segments = []

        # Add leading unused space (for Side B - tape flip logic)
        if unused_duration_offset > 0:
            segments.append(
                MinimapSegment(duration=unused_duration_offset, is_hatched=True)
            )

        # Add track segments
        for track in tape_side.tracks:
            segments.append(
                MinimapSegment(duration=track.duration, track_number=track.track_number)
            )

        # Add trailing unused space
        # Total duration = offset (if Side B) + tracks + trailing
        total_track_duration = sum(track.duration for track in tape_side.tracks)
        total_used_duration = unused_duration_offset + total_track_duration
        trailing_unused = tape_side.max_duration - total_used_duration
        if trailing_unused > 0:
            segments.append(MinimapSegment(duration=trailing_unused, is_hatched=True))

        return segments

    def _draw_minimap(
        self,
        context: RendererContext,
        tape_side: TapeSide,
        x: float,
        y: float,
        width: float,
        height: float,
        unused_duration_offset: float = 0,
    ) -> None:
        """Draw a horizontal visual minimap of track durations for a tape side."""
        if not tape_side.tracks or tape_side.max_duration == 0:
            return

        c = context.canvas

        # Draw border
        c.setStrokeColor(Color(*context.color_scheme.text))
        c.setLineWidth(0.5)
        c.rect(x, y - height, width, height, fill=0)

        # Build segments
        segments = self._build_minimap_segments(tape_side, unused_duration_offset)

        # Render each segment horizontally (left-to-right)
        current_x = x
        track_font_size = 7  # Increased from 6 for better print visibility

        for i, segment in enumerate(segments):
            # Calculate width proportional to duration
            segment_proportion = segment.duration / tape_side.max_duration
            segment_width = width * segment_proportion

            if segment.is_hatched:
                # Draw cross-hatched pattern for empty space
                self._draw_hatched_rect(c, current_x, y - height, segment_width, height)
            else:
                # Draw filled rectangle for track
                c.setFillColor(Color(*context.color_scheme.accent))
                c.rect(current_x, y - height, segment_width, height, fill=1, stroke=0)

                # Draw track number vertically (upright), horizontally centered in segment
                if segment.track_number is not None and segment_width > 5:
                    c.setFillColor(Color(*context.color_scheme.background))
                    # Use bold font for better print visibility
                    c.setFont(f"{context.font_config.monospace_family}-Bold", track_font_size)
                    track_num_str = str(segment.track_number)
                    track_num_width = c.stringWidth(
                        track_num_str, f"{context.font_config.monospace_family}-Bold", track_font_size
                    )

                    # Check if the full track number fits in the segment
                    if track_num_width <= segment_width - 2:  # 2pt padding
                        # Full number fits - draw normally
                        segment_middle_x = current_x + segment_width / 2
                        text_x = segment_middle_x - track_num_width / 2
                        text_y = y - height / 2 - track_font_size / 3  # Vertically center, adjust for baseline
                        c.drawString(text_x, text_y, track_num_str)
                    else:
                        # Not enough space - show last digit with underlines for tens place
                        last_digit = segment.track_number % 10
                        tens_digit = segment.track_number // 10

                        # Draw the last digit
                        last_digit_str = str(last_digit)
                        last_digit_width = c.stringWidth(
                            last_digit_str, f"{context.font_config.monospace_family}-Bold", track_font_size
                        )

                        segment_middle_x = current_x + segment_width / 2
                        text_x = segment_middle_x - last_digit_width / 2
                        text_y = y - height / 2 - track_font_size / 3
                        c.drawString(text_x, text_y, last_digit_str)

                        # Draw underline(s) beneath the digit to represent tens place
                        # Number of underlines = tens digit (1 for 10-19, 2 for 20-29, etc.)
                        if tens_digit > 0:
                            underline_y = text_y - 1  # Position underline just below the digit
                            underline_width = last_digit_width
                            underline_spacing = 1.5  # Spacing between multiple underlines

                            for i in range(tens_digit):
                                c.setLineWidth(0.5)
                                c.line(
                                    text_x,
                                    underline_y - (i * underline_spacing),
                                    text_x + underline_width,
                                    underline_y - (i * underline_spacing)
                                )

            # Draw vertical separator line (but not after the last segment)
            current_x += segment_width
            if i < len(segments) - 1:
                c.setStrokeColor(Color(*context.color_scheme.background))
                c.setLineWidth(0.5)
                c.line(current_x, y - height, current_x, y)

    def _draw_hatched_rect(self, c: Canvas, x: float, y: float, width: float, height: float) -> None:
        """Draw a rectangle with cross-hatch pattern."""
        c.saveState()

        # Draw diagonal hatch lines
        c.setStrokeColor(HexColor(0xcccccc))
        c.setLineWidth(0.25)

        spacing = 2

        # Diagonal lines from bottom-left to top-right
        for i in range(0, int(width + height), spacing):
            x1 = x + i
            y1 = y
            x2 = x
            y2 = y + i

            # Clip to bounds
            if x1 > x + width:
                y1 += (x1 - (x + width))
                x1 = x + width
            if y2 > y + height:
                x2 += (y2 - (y + height))
                y2 = y + height

            c.line(x1, y1, x2, y2)

        # Diagonal lines from top-left to bottom-right (cross-hatch)
        for i in range(0, int(width + height), spacing):
            x1 = x
            y1 = y + height - i
            x2 = x + i
            y2 = y + height

            # Clip to bounds
            if y1 < y:
                x1 += (y - y1)
                y1 = y
            if x2 > x + width:
                y2 -= (x2 - (x + width))
                x2 = x + width

            c.line(x1, y1, x2, y2)

        c.restoreState()

    def _calculate_char_spacing_factor(
        self, text: str, current_width: float, target_width: float
    ) -> float:
        """
        Calculate character spacing factor needed to fit text within target width.

        Args:
            text: Text to fit.
            current_width: Current width of text with charSpace=0.
            target_width: Target width to fit within.

        Returns:
            Character spacing factor (0 = normal, negative = compressed).
        """
        if current_width <= target_width:
            return 0.0  # No compression needed

        # Calculate how much we need to compress
        # Formula: new_width = current_width + (len(text) * char_spacing)
        # We want: target_width = current_width + (len(text) * char_spacing)
        # So: char_spacing = (target_width - current_width) / len(text)
        num_chars = len(text)
        if num_chars == 0:
            return 0.0

        char_spacing = (target_width - current_width) / num_chars
        return char_spacing

    def _fit_track_title_adaptive(
        self, c: Canvas, track_title_text: str,
        line1_available_width: float, line2_available_width: float,
        font_family: str, font_size: float, word_spacing: float, min_char_spacing: float
    ) -> tuple[str, str, float, float]:
        """
        Adaptively fit track title using character spacing compression and smart wrapping.

        Algorithm:
        1. Try single line with normal spacing (charSpace=0)
        2. If doesn't fit, calculate compression factor needed
        3. If factor >= min_char_spacing threshold, use compression
        4. Otherwise, wrap to two lines:
           - Split at word boundary
           - Calculate compression for narrower line
           - Apply same compression to both lines for consistency
           - If still doesn't fit, use min compression and truncate line 2

        Args:
            c: Canvas for measuring text width.
            track_title_text: Track title to fit.
            line1_available_width: Available width for line 1 (after track number, before duration).
            line2_available_width: Available width for line 2 (full width minus indent).
            font_family: Font family name.
            font_size: Font size in points.
            word_spacing: Word spacing adjustment in points.
            min_char_spacing: Minimum character spacing threshold.

        Returns:
            Tuple of (line1_text, line2_text, char_spacing, line2_char_spacing).
            line2_text is empty string if single line fits.
        """
        # Calculate current width with word spacing
        title_width = c.stringWidth(track_title_text, font_family, font_size)
        title_width += track_title_text.count(' ') * word_spacing

        # Step 1: Try single line first
        if title_width <= line1_available_width:
            return (track_title_text, "", 0.0, 0.0)

        # Step 2: Calculate compression factor needed for single line
        char_spacing = self._calculate_char_spacing_factor(
            track_title_text, title_width, line1_available_width
        )

        if char_spacing >= min_char_spacing:
            # Compression is acceptable, use single line
            return (track_title_text, "", char_spacing, 0.0)

        # Step 3: Wrap to two lines
        # Split at word boundary to maximize line 1 usage
        first_line, remainder = self._split_text_for_wrap(
            c, track_title_text, line1_available_width, font_family, font_size, word_spacing
        )

        if not remainder:
            # Entire text fits on line 1 after split (shouldn't happen, but handle it)
            return (first_line, "", 0.0, 0.0)

        # Calculate widths for both lines with word spacing
        line1_width = c.stringWidth(first_line, font_family, font_size)
        line1_width += first_line.count(' ') * word_spacing

        # Line 2 text (without indent - indent will be drawn separately in monospace)
        line2_text = remainder
        line2_width = c.stringWidth(line2_text, font_family, font_size)
        line2_width += line2_text.count(' ') * word_spacing

        # Check if both lines fit with normal spacing
        if line1_width <= line1_available_width and line2_width <= line2_available_width:
            return (first_line, line2_text, 0.0, 0.0)

        # Calculate compression factors for both lines
        line1_char_spacing = self._calculate_char_spacing_factor(
            first_line, line1_width, line1_available_width
        )
        line2_char_spacing = self._calculate_char_spacing_factor(
            line2_text, line2_width, line2_available_width
        )

        # Use compression factor from the narrower line (worst case)
        # Apply same factor to both lines for visual consistency
        unified_char_spacing = min(line1_char_spacing, line2_char_spacing)

        if unified_char_spacing >= min_char_spacing:
            # Both lines can fit with compression
            return (first_line, line2_text, unified_char_spacing, unified_char_spacing)

        # Step 4: Last resort - use min compression and truncate line 2
        # Render line 1 with min compression
        # Truncate line 2 with ellipsis using min compression
        truncated_line2 = self._truncate_with_ellipsis_and_char_spacing(
            c, line2_text, line2_available_width, font_family, font_size,
            word_spacing, min_char_spacing
        )

        return (first_line, truncated_line2, min_char_spacing, min_char_spacing)

    def _truncate_with_ellipsis_and_char_spacing(
        self, c: Canvas, text: str, max_width: float, font_family: str, font_size: float,
        word_spacing: float, char_spacing: float
    ) -> str:
        """
        Truncate text with ellipsis accounting for character spacing.

        Args:
            c: Canvas for measuring text width.
            text: Text to truncate.
            max_width: Maximum width in points.
            font_family: Font family name.
            font_size: Font size in points.
            word_spacing: Word spacing adjustment in points.
            char_spacing: Character spacing to apply.

        Returns:
            Truncated text with ellipsis if needed.
        """
        # Calculate width with char spacing
        text_width = c.stringWidth(text, font_family, font_size)
        text_width += text.count(' ') * word_spacing
        text_width += len(text) * char_spacing

        if text_width <= max_width:
            return text

        # Use single character ellipsis
        ellipsis = "…"
        ellipsis_width = c.stringWidth(ellipsis, font_family, font_size)
        ellipsis_width += char_spacing  # Ellipsis also gets char spacing

        # Available width for actual text (excluding ellipsis)
        available_text_width = max_width - ellipsis_width

        # Binary search for the right length
        left, right = 0, len(text)
        best_length = 0

        while left <= right:
            mid = (left + right) // 2
            truncated_text = text[:mid]
            width = c.stringWidth(truncated_text, font_family, font_size)
            width += truncated_text.count(' ') * word_spacing
            width += len(truncated_text) * char_spacing

            if width <= available_text_width:
                best_length = mid
                left = mid + 1
            else:
                right = mid - 1

        return text[:best_length] + ellipsis

    def _truncate_with_ellipsis(
        self, c: Canvas, text: str, max_width: float, font_family: str, font_size: float,
        word_spacing: float = 0
    ) -> str:
        """
        Truncate text with ellipsis to fit within max_width.

        Args:
            c: Canvas for measuring text width.
            text: Text to truncate.
            max_width: Maximum width in points.
            font_family: Font family name.
            font_size: Font size in points.
            word_spacing: Word spacing adjustment in points.

        Returns:
            Truncated text with ellipsis if needed.
        """
        # If text already fits, return as-is
        text_width = c.stringWidth(text, font_family, font_size) + text.count(' ') * word_spacing
        if text_width <= max_width:
            return text

        # Use single character ellipsis
        ellipsis = "…"
        ellipsis_width = c.stringWidth(ellipsis, font_family, font_size)

        # Available width for actual text (excluding ellipsis)
        available_text_width = max_width - ellipsis_width

        # Binary search for the right length
        left, right = 0, len(text)
        best_length = 0

        while left <= right:
            mid = (left + right) // 2
            truncated_text = text[:mid]
            width = c.stringWidth(truncated_text, font_family, font_size)
            width += truncated_text.count(' ') * word_spacing

            if width <= available_text_width:
                best_length = mid
                left = mid + 1
            else:
                right = mid - 1

        return text[:best_length] + ellipsis

    def _split_text_for_wrap(
        self, c: Canvas, text: str, max_width: float, font_family: str, font_size: float,
        word_spacing: float = 0
    ) -> tuple[str, str]:
        """
        Split text into two parts: what fits on first line and remainder.

        Args:
            c: Canvas for measuring text width.
            text: Text to split.
            max_width: Maximum width for first part in points.
            font_family: Font family name.
            font_size: Font size in points.
            word_spacing: Word spacing adjustment in points.

        Returns:
            Tuple of (first_line, remainder).
        """
        # Try to split at word boundaries
        words = text.split()
        first_line = ""
        remainder = text

        for i, word in enumerate(words):
            test_line = " ".join(words[:i+1])
            width = c.stringWidth(test_line, font_family, font_size)
            width += test_line.count(' ') * word_spacing

            if width <= max_width:
                first_line = test_line
                remainder = " ".join(words[i+1:])
            else:
                break

        # If no words fit, just split at character boundary
        if not first_line:
            for i in range(len(text), 0, -1):
                test_text = text[:i]
                width = c.stringWidth(test_text, font_family, font_size)
                width += test_text.count(' ') * word_spacing
                if width <= max_width:
                    first_line = test_text
                    remainder = text[i:]
                    break

        return first_line, remainder
