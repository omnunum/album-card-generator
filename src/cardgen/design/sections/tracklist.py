"""Tracklist section implementation."""

from reportlab.lib.colors import Color

from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions
from cardgen.utils.tape import TapeSide


class TracklistSection(CardSection):
    """Tracklist section with Side A/B and duration minimap."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        side_a: TapeSide,
        side_b: TapeSide,
        title: str = "Tracklist",
    ) -> None:
        """
        Initialize tracklist section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            side_a: Tape Side A with tracks.
            side_b: Tape Side B with tracks.
            title: Section title.
        """
        super().__init__(name, dimensions)
        self.side_a = side_a
        self.side_b = side_b
        self.title = title

    def render(self, context: RendererContext) -> None:
        """Render track listing with Side A/B and duration minimap."""
        c = context.canvas

        # Minimap bar width on right side
        minimap_width = 20  # points
        minimap_gap = 8  # gap between tracklist and minimap

        c.setFillColor(Color(*context.color_scheme.text))

        # Title
        c.setFont(
            f"{context.font_config.family}-Bold", context.font_config.title_size
        )
        text_y = context.y + context.height - context.padding - context.font_config.title_size
        c.drawString(context.x + context.padding, text_y, self.title)

        c.setFont(context.font_config.family, context.font_config.track_size)
        text_y -= context.font_config.track_size + 10

        # Available width for track text (leaving room for minimap)
        text_width = context.width - (context.padding * 2) - minimap_width - minimap_gap

        # Render Side A
        if self.side_a and self.side_a.tracks:
            text_y = self._render_tape_side(
                context, self.side_a, "Side A", text_y, text_width, minimap_width
            )
            text_y -= 6  # Extra gap between sides

        # Render Side B
        if self.side_b and self.side_b.tracks:
            # Check if there's room for Side B header
            if text_y >= context.y + context.padding + context.font_config.track_size:
                text_y = self._render_tape_side(
                    context, self.side_b, "Side B", text_y, text_width, minimap_width
                )

    def _render_tape_side(
        self,
        context: RendererContext,
        tape_side: TapeSide,
        label: str,
        text_y: float,
        text_width: float,
        minimap_width: float,
    ) -> float:
        """
        Render a single tape side (A or B) with tracks and minimap.

        Args:
            context: Rendering context.
            tape_side: Tape side to render.
            label: Label to display ("Side A" or "Side B").
            text_y: Current y position for text.
            text_width: Available width for track text.
            minimap_width: Width of minimap bar.

        Returns:
            Updated text_y position after rendering.
        """
        c = context.canvas

        # Ensure text color is set (fixes white text bug for Side B)
        c.setFillColor(Color(*context.color_scheme.text))

        # Side header
        c.setFont(
            f"{context.font_config.family}-Bold", context.font_config.track_size
        )
        c.drawString(context.x + context.padding, text_y, label)
        text_y -= context.font_config.track_size + 4

        # Side tracks
        c.setFont(context.font_config.family, context.font_config.track_size)
        side_start_y = text_y

        for track in tape_side.tracks:
            if text_y < context.y + context.padding + context.font_config.track_size:
                break

            track_text = f"{track.track_number}. {track.title}"
            duration_text = track.format_duration()

            # Draw track number and title
            c.drawString(context.x + context.padding, text_y, track_text)

            # Draw duration (before minimap)
            duration_width = c.stringWidth(
                duration_text,
                context.font_config.family,
                context.font_config.track_size,
            )
            c.drawString(
                context.x + context.padding + text_width - duration_width,
                text_y,
                duration_text,
            )

            text_y -= context.font_config.track_size + 3

        side_end_y = text_y

        # Draw minimap
        self._draw_minimap(
            context,
            tape_side,
            context.x + context.width - context.padding - minimap_width,
            side_start_y,
            minimap_width,
            side_start_y - side_end_y,
        )

        return text_y

    def _draw_minimap(
        self,
        context: RendererContext,
        tape_side: TapeSide,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        """Draw a visual minimap of track durations for a tape side."""
        if not tape_side.tracks or tape_side.max_duration == 0:
            return

        c = context.canvas

        # Draw border
        c.setStrokeColor(Color(*context.color_scheme.text))
        c.setLineWidth(0.5)
        c.rect(x, y - height, width, height, fill=0)

        # Calculate proportional heights for each track
        # Start from top and go down
        current_y = y
        track_font_size = 6

        for track in tape_side.tracks:
            # Calculate height proportional to duration
            track_proportion = track.duration / tape_side.max_duration
            track_height = height * track_proportion

            # Draw filled rectangle for this track (going down from current_y)
            c.setFillColor(Color(*context.color_scheme.accent))
            c.rect(x, current_y - track_height, width, track_height, fill=1, stroke=0)

            # Draw track number in the middle of the bar
            c.setFillColor(Color(*context.color_scheme.background))
            c.setFont(context.font_config.family, track_font_size)
            track_num_str = str(track.track_number)
            track_num_width = c.stringWidth(
                track_num_str, context.font_config.family, track_font_size
            )

            # FIX: Lower threshold from 8 to 5 to show more track numbers
            if track_height > 5:
                c.drawString(
                    x + (width - track_num_width) / 2,
                    current_y - track_height + (track_height - track_font_size) / 2,
                    track_num_str,
                )

            # Draw separator line between tracks
            current_y -= track_height
            c.setStrokeColor(Color(*context.color_scheme.text))
            c.setLineWidth(0.25)
            c.line(x, current_y, x + width, current_y)
