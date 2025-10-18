"""Default theme implementation."""

from cardgen.config import DefaultThemeConfig
from cardgen.design.base import ColorScheme, FontConfig, Theme
from cardgen.fonts import is_iosevka_available


class DefaultTheme(Theme):
    """Default clean theme for j-cards."""

    def __init__(self, config: DefaultThemeConfig | None = None) -> None:
        """
        Initialize default theme.

        Args:
            config: Theme configuration from config file. If None, uses defaults.
        """
        if config is None:
            from cardgen.config import DefaultThemeConfig

            config = DefaultThemeConfig()

        self.config = config

    def get_font_config(self) -> FontConfig:
        """
        Get font configuration for this theme.

        Returns:
            FontConfig object.
        """
        # Use Iosevka if available, otherwise fall back to Courier
        monospace_family = self.config.monospace_font_family
        if monospace_family == "Iosevka" and not is_iosevka_available():
            monospace_family = "Courier"

        return FontConfig(
            family=self.config.font_family,
            monospace_family=monospace_family,
            title_size=self.config.title_font_size,
            artist_size=self.config.artist_font_size,
            track_size=self.config.track_font_size,
            metadata_size=self.config.metadata_font_size,
        )

    def get_color_scheme(self) -> ColorScheme:
        """
        Get color scheme for this theme.

        Returns:
            ColorScheme object.
        """
        return ColorScheme(
            background=tuple(self.config.background_color),  # type: ignore
            text=tuple(self.config.text_color),  # type: ignore
            accent=tuple(self.config.accent_color),  # type: ignore
        )

    def get_padding(self) -> float:
        """
        Get default padding in inches.

        Returns:
            Padding in inches.
        """
        return 0.125  # 1/8 inch padding

    def get_track_title_overflow(self) -> str:
        """
        Get track title overflow mode for tracklists.

        Returns:
            "truncate" or "wrap".
        """
        return self.config.track_title_overflow
