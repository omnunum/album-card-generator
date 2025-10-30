"""Generic j-card layout with configurable panels."""

from cardgen.api.models import Album
from cardgen.config import Theme
from cardgen.design.base import Card, CardSection
from cardgen.utils.dimensions import JCARD_HEIGHT, Dimensions


class JCard(Card):
    """
    Generic j-card layout with configurable panels.

    Panels are laid out left-to-right. Fold lines are automatically generated between panels.
    """

    def __init__(
        self,
        album: Album,
        theme: Theme,
        panels: list[CardSection],
        tape_length_minutes: int = 90,
    ) -> None:
        """
        Initialize j-card with custom panels.

        Args:
            album: Album data to display.
            theme: Theme for styling.
            panels: List of sections to use as panels (left to right).
            tape_length_minutes: Length of cassette tape in minutes (default: 90 for C90).
        """
        super().__init__(album, theme, tape_length_minutes)
        self.panels = panels

        # Calculate positions for each panel
        self._layout_panels()

    def _layout_panels(self) -> None:
        """Layout panels left-to-right, updating their x positions."""
        x_offset = 0.0
        for panel in self.panels:
            # Update panel position
            panel.dimensions.x = x_offset
            panel.dimensions.y = 0.0
            x_offset += panel.dimensions.width

    def get_dimensions(self) -> Dimensions:
        """
        Get overall card dimensions.

        Returns:
            Dimensions object for entire card.
        """
        total_width = sum(panel.dimensions.width for panel in self.panels)
        return Dimensions(width=total_width, height=JCARD_HEIGHT)

    def get_sections(self) -> list[CardSection]:
        """
        Get all sections that make up this card.

        Returns:
            List of CardSection objects with content specifications.
        """
        return self.panels

    def get_fold_lines(self) -> list[float]:
        """
        Get x-coordinates of fold lines (in inches from left edge).

        Returns:
            List of x-coordinates for fold lines (between each panel).
        """
        fold_lines = []
        x_offset = 0.0

        # Add fold line after each panel except the last
        for panel in self.panels[:-1]:
            x_offset += panel.dimensions.width
            fold_lines.append(x_offset)

        return fold_lines
