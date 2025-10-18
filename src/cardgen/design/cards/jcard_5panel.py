"""5-panel cassette j-card with genre/descriptors panel."""

from cardgen.api.models import Album
from cardgen.design.base import Theme
from cardgen.design.cards.jcard import JCard
from cardgen.design.sections import (
    CoverSection,
    GenreDescriptorsSection,
    MetadataSection,
    SpineSection,
    TracklistSection,
)
from cardgen.design.sections.spine import SpineTextItem
from cardgen.utils.dimensions import (
    JCARD_BACK_WIDTH,
    JCARD_HEIGHT,
    JCARD_PANEL_WIDTH,
    JCARD_SPINE_WIDTH,
    Dimensions,
)
from cardgen.utils.tape import split_tracks_by_tape_sides


def create_jcard_5panel(
    album: Album, theme: Theme, tape_length_minutes: int = 90
) -> JCard:
    """
    Create a 5-panel j-card with genre/descriptors panel.

    Layout (left to right): Back | Spine | Front | Inside (Tracklist) | Genre/Descriptors

    Args:
        album: Album data to display.
        theme: Theme for styling.
        tape_length_minutes: Length of cassette tape in minutes (default: 90 for C90).

    Returns:
        JCard with 5 panels configured.
    """
    # Split tracks into tape sides
    side_a, side_b = split_tracks_by_tape_sides(album.tracks, tape_length_minutes)

    # Define panel widths
    genre_panel_width = JCARD_PANEL_WIDTH  # Full-size panel (2.5") for genre/descriptors

    # Create sections for each panel
    panels = []

    # Panel 1: Back (Metadata)
    panels.append(
        MetadataSection(
            name="back",
            dimensions=Dimensions(width=JCARD_BACK_WIDTH, height=JCARD_HEIGHT),
            album=album,
            font_size=9.0,
            padding_override=0.02,
        )
    )

    # Panel 2: Spine
    spine_items: list[SpineTextItem] = []
    spine_items.append(SpineTextItem(text=album.artist))
    spine_items.append(SpineTextItem(text=album.title, bold=True))
    if album.year:
        spine_items.append(SpineTextItem(text=str(album.year)))

    panels.append(
        SpineSection(
            name="spine",
            dimensions=Dimensions(width=JCARD_SPINE_WIDTH, height=JCARD_HEIGHT),
            text_lines=spine_items,
            cover_art=album.cover_art,
        )
    )

    # Panel 3: Front (Cover)
    panels.append(
        CoverSection(
            name="front",
            dimensions=Dimensions(width=JCARD_PANEL_WIDTH, height=JCARD_HEIGHT),
            cover_art=album.cover_art,
            title=album.title,
            artist=album.artist,
        )
    )

    # Panel 4: Inside (Tracklist)
    panels.append(
        TracklistSection(
            name="inside",
            dimensions=Dimensions(width=JCARD_PANEL_WIDTH, height=JCARD_HEIGHT),
            side_a=side_a,
            side_b=side_b,
            title="Tracklist",
            track_title_overflow=theme.get_track_title_overflow(),
        )
    )

    # Panel 5: Genre/Descriptors (full-size horizontal layout)
    panels.append(
        GenreDescriptorsSection(
            name="genre_descriptors",
            dimensions=Dimensions(width=genre_panel_width, height=JCARD_HEIGHT),
            album=album,
            font_size=10.0,  # Larger since we have full 2.5" width
            padding_override=0.125,  # Standard padding
        )
    )

    return JCard(album, theme, panels, tape_length_minutes)
