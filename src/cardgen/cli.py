"""CLI interface for album card generator."""

from pathlib import Path

import click

from cardgen.api import NavidromeClient
from cardgen.config import format_output_name, load_config
from cardgen.design import JCard4Panel
from cardgen.design.themes import DefaultTheme
from cardgen.render import PDFRenderer
from cardgen.utils.dimensions import PAGE_SIZES


@click.group()
@click.version_option()
def main() -> None:
    """Generate printable cassette j-cards from Navidrome albums and playlists."""
    pass


@main.command()
@click.argument("url")
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
    help="Card type override (jcard_4panel). Uses config default if not specified.",
)
@click.option(
    "--theme",
    type=str,
    help="Theme override (default). Uses config default if not specified.",
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
def album(
    url: str,
    output: Path | None,
    output_name: str,
    config: Path | None,
    card_type: str | None,
    theme: str | None,
    dpi: int | None,
    no_crop_marks: bool,
    page_size: str | None,
    tape_length: int,
) -> None:
    """
    Generate j-card from Navidrome album.

    URL can be either:
    - Simple format: album/abc123
    - Full URL: http://server/app/#/album/abc123
    """
    try:
        # Load configuration
        cfg = load_config(config)

        # Extract album ID from URL
        resource_type, resource_id = NavidromeClient.extract_id_from_url(url)

        if resource_type != "album":
            click.echo(f"Error: URL is for a {resource_type}, not an album. Use `cardgen playlist` instead.", err=True)
            raise SystemExit(1)

        # Initialize Navidrome client
        client = NavidromeClient(cfg.navidrome)

        # Fetch album data
        click.echo(f"Fetching album {resource_id}...")
        album_data = client.get_album(resource_id)
        click.echo(f"Found: {album_data.artist} - {album_data.title}")

        # Determine output path
        if output is None:
            template = cfg.output.templates.model_dump().get(output_name)
            if template is None:
                click.echo(f"Error: Unknown output template '{output_name}'", err=True)
                raise SystemExit(1)

            output_filename = format_output_name(
                template,
                album_data.artist,
                album_data.title,
                album_data.year,
            )
            output = Path(output_filename)

        # Select card type
        card_type = card_type or cfg.output.default_card_type
        if card_type != "jcard_4panel":
            click.echo(f"Error: Unsupported card type '{card_type}'. Currently only 'jcard_4panel' is supported.", err=True)
            raise SystemExit(1)

        # Select theme
        theme_name = theme or cfg.output.default_theme
        if theme_name == "default":
            theme_obj = DefaultTheme(cfg.themes.default)
        else:
            click.echo(f"Error: Unknown theme '{theme_name}'. Currently only 'default' is supported.", err=True)
            raise SystemExit(1)

        # Create card
        card = JCard4Panel(album_data, theme_obj, tape_length_minutes=tape_length)

        # Render PDF
        render_dpi = dpi or cfg.output.dpi
        include_marks = not no_crop_marks if no_crop_marks else cfg.output.include_crop_marks
        selected_page_size = page_size or cfg.output.default_page_size

        renderer = PDFRenderer(dpi=render_dpi, include_crop_marks=include_marks, page_size=selected_page_size)

        click.echo(f"Generating PDF at {render_dpi} DPI on {selected_page_size} page...")
        renderer.render_card(card, output)

        click.echo(f"✓ J-card saved to: {output}")

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
