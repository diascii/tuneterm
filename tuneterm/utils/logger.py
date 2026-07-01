import logging
import logging.handlers
import os
import sys
import threading

_LOG_FILE = r"D:\tuneterm\tuneterm.log"


class _FlushRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler that flushes immediately on every emit."""
    def emit(self, record):
        super().emit(record)
        self.flush()


def _ensure_log_dir(path: str) -> None:
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)


def setup_logger():
    _ensure_log_dir(_LOG_FILE)

    logger = logging.getLogger("tuneterm")
    logger.setLevel(logging.DEBUG)

    # Remove any pre-existing handlers to avoid duplicates on re-init
    logger.handlers.clear()

    # ── Rotating file handler (max 5 MB, 3 backups, immediate flush) ──
    file_handler = _FlushRotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
        )
    )
    logger.addHandler(file_handler)

    # ── Console handler (WARNING+) ──
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

    # ── Log uncaught exceptions ──
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_exception

    # ── Hook for threads ──
    def handle_thread_exception(args):
        logger.error(
            "Uncaught thread exception in %s",
            args.thread.name if args.thread else "Unknown",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    threading.excepthook = handle_thread_exception

    return logger


# Automatically initialize on import
logger = setup_logger()
