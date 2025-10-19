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
        """
        super().__init__(name, dimensions)
        self.side_a = side_a
        self.side_b = side_b
        self.title = title
        self.track_title_overflow = track_title_overflow

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

        # Draw minimap aligned with the label baseline
        # The minimap's top should align with the top of the text
        minimap_top_y = text_y + track_size * 0.75  # Align minimap vertically with label (raised slightly)
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

            # Calculate widths for track number (monospace) and title (regular font)
            track_num_width = c.stringWidth(track_num_text, context.font_config.monospace_family, track_size)
            track_title_width = c.stringWidth(track_title_text, context.font_config.family, track_size)
            # Account for word spacing compression in track title
            track_title_width += track_title_text.count(' ') * word_spacing

            # Total track text width
            track_text_width = track_num_width + track_title_width

            # Handle overflow based on mode
            if track_text_width > available_track_width:
                if self.track_title_overflow == "truncate":
                    # Truncate with ellipsis - only truncate the title, not the track number
                    available_for_title = available_track_width - track_num_width
                    truncated_title = self._truncate_with_ellipsis(
                        c, track_title_text, available_for_title,
                        context.font_config.family, track_size, word_spacing
                    )

                    # Draw track number in monospace
                    c.setFont(context.font_config.monospace_family, track_size)
                    c.drawString(context.x + context.padding, text_y, track_num_text)

                    # Draw truncated title in regular font
                    c.setFont(context.font_config.family, track_size)
                    c.drawString(context.x + context.padding + track_num_width, text_y, truncated_title, wordSpace=word_spacing)
                else:  # wrap
                    # Draw first line and wrap continuation
                    # Calculate how much of the title fits on first line
                    available_for_title = available_track_width - track_num_width

                    first_line, remainder = self._split_text_for_wrap(
                        c, track_title_text, available_for_title,
                        context.font_config.family, track_size, word_spacing
                    )

                    # Draw track number in monospace
                    c.setFont(context.font_config.monospace_family, track_size)
                    c.drawString(context.x + context.padding, text_y, track_num_text)

                    # Draw first line of title in regular font
                    c.setFont(context.font_config.family, track_size)
                    c.drawString(context.x + context.padding + track_num_width, text_y, first_line, wordSpace=word_spacing)

                    # Draw continuation on next line if there's a remainder
                    if remainder:
                        text_y -= track_size + line_spacing
                        indent = "   "  # 3 spaces for indent
                        continuation_text = self._truncate_with_ellipsis(
                            c, indent + remainder, available_track_width,
                            context.font_config.family, track_size, word_spacing
                        )
                        c.setFont(context.font_config.family, track_size)
                        c.drawString(context.x + context.padding, text_y, continuation_text, wordSpace=word_spacing)
            else:
                # No overflow, draw normally
                # Draw track number in monospace
                c.setFont(context.font_config.monospace_family, track_size)
                c.drawString(context.x + context.padding, text_y, track_num_text)

                # Draw track title in regular font
                c.setFont(context.font_config.family, track_size)
                c.drawString(context.x + context.padding + track_num_width, text_y, track_title_text, wordSpace=word_spacing)

            # Draw duration in monospace font
            c.setFont(context.font_config.monospace_family, track_size)
            c.drawString(duration_x, text_y, duration_text)

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

                    # Horizontally center in segment, vertically center in minimap bar
                    segment_middle_x = current_x + segment_width / 2
                    text_x = segment_middle_x - track_num_width / 2
                    text_y = y - height / 2 - track_font_size / 3  # Vertically center, adjust for baseline
                    c.drawString(
                        text_x,
                        text_y,
                        track_num_str,
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
