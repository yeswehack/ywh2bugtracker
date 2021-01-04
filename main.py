from __future__ import annotations

import sys

import urllib3  # type: ignore

from ywh2bt.gui.main import run as run_gui

if __name__ == '__main__':
    run_gui(*sys.argv)
