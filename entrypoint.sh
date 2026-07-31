#!/bin/bash
set -e

# xvfb-run starts a virtual X server, sets DISPLAY, runs the command, then
# tears the display down. watchdog.py spawns download_config.py as a
# subprocess, which inherits DISPLAY from this same shell, so Chromium
# launched with headless=False in either process finds a screen to render to.
exec xvfb-run -a --server-args="-screen 0 1920x1080x24" python watchdog.py
