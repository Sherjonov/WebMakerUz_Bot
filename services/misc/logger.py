"""Logging sozlamasi."""
import contextlib
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    # Windows konsolida emoji/o'zbekcha harflar xato bermasligi uchun
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(Exception):
            stream.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
