"""CLI interface for album card generator."""

from pathlib import Path

import click

from cardgen.api import NavidromeClient
from cardgen.config import format_output_name, load_config
from cardgen.design import JCard4Panel, create_jcard_5panel
from cardgen.design.themes import DefaultTheme
from cardgen.fonts import register_fonts
from cardgen.render import PDFRenderer
from cardgen.utils.dimensions import PAGE_SIZES


@click.group()
@click.version_option()
def main() -> None:
    """Generate printable cassette j-cards from Navidrome albums and playlists."""
    # Register custom fonts at startup
    register_fonts()


@main.command()
@click.argument("urls", nargs=-1, required=True)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output PDF file path. If not specified, uses template from config.",
)
@click.option(
    "--output-name",
    type=str,
    default="default",
    help="Named output template from config (default, dated, simple).",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config.toml file. Defaults to ./config.toml",
)
@click.option(
    "--card-type",
    type=str,
    help="Card type override (jcard_4panel, jcard_5panel). Uses config default if not specified.",
)
@click.option(
    "--gradient",
    is_flag=True,
    help="Use gradient background with colors extracted from album art.",
)
@click.option(
    "--dpi",
    type=int,
    help="DPI for image rendering (300-1200). Uses config default if not specified.",
)
@click.option(
    "--no-crop-marks",
    is_flag=True,
    help="Disable crop marks and fold guides.",
)
@click.option(
    "--page-size",
    type=click.Choice(list(PAGE_SIZES.keys()), case_sensitive=False),
    help="Page size for printing.",
)
@click.option(
    "--tape-length",
    type=int,
    default=90,
    help="Cassette tape length in minutes (default: 90 for C90).",
)
@click.option(
    "--cover-art-mode",
    type=click.Choice(["square", "fullscale"], case_sensitive=False),
    help="Album art display mode: 'square' (default) or 'fullscale' (top-to-bottom with crop).",
)
@click.option(
    "--cover-art-align",
    type=click.Choice(["center", "left", "right"], case_sensitive=False),
    help="Horizontal alignment for fullscale mode: 'center' (default), 'left', or 'right'.",
)
def album(
    urls: tuple[str, ...],
    output: Path | None,
    output_name: str,
    config: Path | None,
    card_type: str | None,
    gradient: bool,
    dpi: int | None,
    no_crop_marks: bool,
    page_size: str | None,
    tape_length: int,
    cover_art_mode: str | None,
    cover_art_align: str | None,
) -> None:
    """
    Generate j-cards from one or more Navidrome albums.

    Cards are stacked vertically (2 per page) for efficient printing.

    URL can be either:
    - Simple format: album/abc123
    - Full URL: http://server/app/#/album/abc123

    Multiple albums can be specified to print on one PDF.
    """
    try:
        # Load configuration
        cfg = load_config(config)

        # Initialize Navidrome client
        client = NavidromeClient(cfg.navidrome)

        # Fetch all albums
        albums = []
        for url in urls:
            # Extract album ID from URL
            resource_type, resource_id = NavidromeClient.extract_id_from_url(url)

            if resource_type != "album":
                click.echo(f"Error: URL is for a {resource_type}, not an album. Use `cardgen playlist` instead.", err=True)
                raise SystemExit(1)

            # Fetch album data
            click.echo(f"Fetching album {resource_id}...")
            album_data = client.get_album(resource_id)
            click.echo(f"  Found: {album_data.artist} - {album_data.title}")
            albums.append(album_data)

        # Determine output path
        if output is None:
            template = cfg.output.templates.model_dump().get(output_name)
            if template is None:
                click.echo(f"Error: Unknown output template '{output_name}'", err=True)
                raise SystemExit(1)

            # Use first album for filename
            output_filename = format_output_name(
                template,
                albums[0].artist,
                albums[0].title,
                albums[0].year,
            )
            # If multiple albums, add suffix
            if len(albums) > 1:
                output_filename = output_filename.replace(".pdf", f"_and_{len(albums)-1}_more.pdf")
            output = Path(output_filename)

        # Select card type
        selected_card_type = card_type or cfg.output.default_card_type
        if selected_card_type not in ("jcard_4panel", "jcard_5panel"):
            click.echo(f"Error: Unsupported card type '{selected_card_type}'. Supported: jcard_4panel, jcard_5panel", err=True)
            raise SystemExit(1)

        # Create cards for each album with optional gradient
        cards = []

        for album_data in albums:
            # Create theme config with gradient enabled if flag is set
            theme_config = cfg.themes.default
            updates = {}
            if gradient:
                updates["use_gradient"] = True
            if cover_art_mode:
                updates["cover_art_mode"] = cover_art_mode
            if cover_art_align:
                updates["cover_art_align"] = cover_art_align

            if updates:
                theme_config = theme_config.model_copy(update=updates)

            # Create theme (pass cover art for gradient extraction)
            theme_obj = DefaultTheme(theme_config, cover_art=album_data.cover_art)

            # Create card with theme
            if selected_card_type == "jcard_4panel":
                card = JCard4Panel(album_data, theme_obj, tape_length_minutes=tape_length)
            else:  # jcard_5panel
                card = create_jcard_5panel(album_data, theme_obj, tape_length_minutes=tape_length)
            cards.append(card)

        # Render PDF
        render_dpi = dpi or cfg.output.dpi
        include_marks = not no_crop_marks if no_crop_marks else cfg.output.include_crop_marks
        selected_page_size = page_size or cfg.output.default_page_size

        renderer = PDFRenderer(dpi=render_dpi, include_crop_marks=include_marks, page_size=selected_page_size)

        click.echo(f"Generating PDF with {len(cards)} card(s) at {render_dpi} DPI on {selected_page_size} page...")
        renderer.render_cards(cards, output)

        click.echo(f"✓ J-card(s) saved to: {output}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("url")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output PDF file path.",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config.toml file. Defaults to ./config.toml",
)
def playlist(url: str, output: Path | None, config: Path | None) -> None:
    """
    Generate j-card from Navidrome playlist URL (NOT YET IMPLEMENTED).

    URL should be the full web interface URL, e.g.:
    http://server/app/#/playlist/xyz789
    """
    click.echo("Error: Playlist support is not yet implemented.", err=True)
    click.echo("Use `cardgen album` for now.", err=True)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
