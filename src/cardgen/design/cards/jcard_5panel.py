"""5-panel cassette j-card layout implementation."""

from cardgen.api.models import Album
from cardgen.config import Theme
from cardgen.design.base import Card, CardSection
from cardgen.design.sections import CoverSection, MetadataSection, SpineSection, TracklistSection
from cardgen.design.sections.descriptors import DescriptorsSection
from cardgen.design.sections.genre_tree import GenreTreeSection
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import (
    JCARD_5_PANEL_HEIGHT,
    JCARD_5_PANEL_WIDTH,
    JCARD_BACK_WIDTH,
    JCARD_HEIGHT,
    JCARD_PANEL_WIDTH,
    JCARD_SPINE_WIDTH,
    Dimensions,
)
from cardgen.utils.tape import assign_tape_sides


class JCard5Panel(Card):
    """
    5-panel cassette j-card layout.

    Layout (left to right): Back | Spine | Front | Inside | Genre/Descriptors
    When folded, back wraps around outside back, front is on outside front, inside opens to reveal genre panel.
    """

    def __init__(self, album: Album, theme: Theme, album_art: AlbumArt | None, tape_length_minutes: int = 90) -> None:
        """
        Initialize 5-panel j-card.

        Args:
            album: Album data to display.
            theme: Theme for styling.
            album_art: AlbumArt object for image processing.
            tape_length_minutes: Length of cassette tape in minutes (default: 90 for C90).
        """
        super().__init__(album, theme, tape_length_minutes)
        self.album_art = album_art

        # Renumber tracks sequentially (handles multi-disc albums where tracks may have duplicate numbers)
        for i, track in enumerate(album.tracks, start=1):
            track.track_number = i

        # Assign tracks to tape sides (modifies tracks in place)
        self.side_capacity = assign_tape_sides(album.tracks, tape_length_minutes)

    def get_dimensions(self) -> Dimensions:
        """
        Get overall card dimensions.

        Returns:
            Dimensions object for entire card.
        """
        return Dimensions(width=JCARD_5_PANEL_WIDTH, height=JCARD_5_PANEL_HEIGHT)

    def get_sections(self) -> list[CardSection]:
        """
        Get all sections that make up this card.

        Returns:
            List of CardSection objects with content specifications.
        """
        sections: list[CardSection] = []

        # Calculate x positions for each panel
        panel_1_x = 0.0  # Back
        panel_2_x = JCARD_BACK_WIDTH  # Spine
        panel_3_x = JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH  # Front
        panel_4_x = JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH  # Inside
        panel_5_x = JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH + JCARD_PANEL_WIDTH  # Genre/Descriptors

        # Panel 1: Back (Metadata)
        sections.append(
            MetadataSection(
                name="back",
                dimensions=Dimensions(
                    width=JCARD_BACK_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_1_x,
                    y=0.0
                ),
                album=self.album,
                font_size=9.0,
                padding=1/16  # Match double album padding
            )
        )

        # Panel 2: Spine (Artist, Title, Year - all bold)
        sections.append(
            SpineSection(
                name="spine",
                dimensions=Dimensions(
                    width=JCARD_SPINE_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_2_x,
                    y=0.0
                ),
                text_lines=[" • ".join([self.album.artist, self.album.title, str(self.album.year)])],
                album_art_right=self.album_art,
                show_dolby_logo=self.album.show_dolby_logo,
            )
        )

        # Panel 3: Front (Cover)
        sections.append(
            CoverSection(
                name="front",
                dimensions=Dimensions(
                    width=JCARD_PANEL_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_3_x,
                    y=0.0
                ),
                album_art=self.album_art,
                title=self.album.title,
                artist=self.album.artist,
                show_dolby_logo=self.album.show_dolby_logo,
            )
        )

        # Panel 4: Inside (Tracklist)
        sections.append(
            TracklistSection(
                name="inside",
                dimensions=Dimensions(
                    width=JCARD_PANEL_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_4_x,
                    y=0.0
                ),
                tracks=self.album.tracks,
                side_capacity=self.side_capacity,
                title="Tracklist",
                track_title_overflow=self.theme.track_title_overflow,
                min_track_title_char_spacing=self.theme.min_track_title_char_spacing,
            )
        )

        # Panel 5: Split vertically 50/50 - Genre Tree (top) and Descriptors (bottom)

        # Genre tree at top: 50% of height = 2.0", positioned at y=2.0"
        genre_tree_height = JCARD_HEIGHT * 0.5
        genre_tree_y = JCARD_HEIGHT * 0.5  # Top half

        sections.append(
            GenreTreeSection(
                name="genre_tree",
                dimensions=Dimensions(
                    width=JCARD_PANEL_WIDTH,
                    height=genre_tree_height,
                    x=panel_5_x,
                    y=genre_tree_y
                ),
                album=self.album,
                font_size=10.0,
                padding=1/16,
            )
        )

        # Descriptors at bottom: 50% of height = 2.0", positioned at y=0.0"
        descriptors_height = JCARD_HEIGHT * 0.5
        descriptors_y = 0.0  # Bottom half

        sections.append(
            DescriptorsSection(
                name="descriptors",
                dimensions=Dimensions(
                    width=JCARD_PANEL_WIDTH,
                    height=descriptors_height,
                    x=panel_5_x,
                    y=descriptors_y
                ),
                album=self.album,
                font_size=10.0,
                padding=1/16,
            )
        )


        return sections

    def get_fold_lines(self) -> list[float]:
        """
        Get x-coordinates of fold lines (in inches from left edge).

        Returns:
            List of x-coordinates for fold lines.
        """
        # Fold lines between each panel
        # Back (0.667") | Spine (0.5") | Front (2.5") | Inside (2.5") | Genre/Descriptors (2.5")
        return [
            # JCARD_BACK_WIDTH,  # Between back and spine
            # JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH,  # Between spine and front
            # JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH,  # Between front and inside
            JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH + JCARD_PANEL_WIDTH,  # Between inside and genre panel
        ]
