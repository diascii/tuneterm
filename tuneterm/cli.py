import logging
import signal

import click
import tuneterm.utils.logger  # Initialize logger before UI takes over
from tuneterm.ui.app import TuneTermApp
from tuneterm.utils.config import config


def _handle_sigterm(signum, frame):
    logging.getLogger("tuneterm").warning(
        "[SIGNAL] Received signal %s, shutting down", signum
    )
    raise SystemExit(0)


# Install signal handler for graceful shutdown
signal.signal(signal.SIGTERM, _handle_sigterm)


@click.group(invoke_without_command=True)
@click.option('--dir', type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Start TuneTerm with a specific music directory.')
@click.pass_context
def main(ctx, dir):
    """TuneTerm - Professional terminal music player."""
    if ctx.invoked_subcommand is None:
        app = TuneTermApp(music_dir=dir)
        app.run()

@main.command()
@click.argument('filepath', type=click.STRING)
def play(filepath):
    """Play a specific file or URL immediately."""
    app = TuneTermApp(play_on_start=filepath)
    app.run()
