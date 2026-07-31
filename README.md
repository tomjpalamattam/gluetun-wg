# gluetun-config-refresher

A watchdog sidecar for a `gluetun` + `tailscale` exit-node stack. Polls
gluetun's Docker healthcheck, and if it goes unhealthy, re-downloads a fresh
PureVPN WireGuard config via Playwright and restarts gluetun.

## Layout

```
.
├── .github/workflows/build.yml   # CI: builds & pushes image to GHCR on push to main
├── Dockerfile                    # python:3.12-slim + Xvfb + Chromium
├── entrypoint.sh                 # runs watchdog.py under xvfb-run
├── download_config.py            # Playwright script: logs into PureVPN, downloads wg0.conf
├── watchdog.py                   # polls gluetun's health, triggers refresh + restart
├── requirements.txt
├── docker-compose.yml            # full stack: gluetun + tailscale + this sidecar
├── .env.example                  # copy to .env and fill in real secrets
├── build.sh                      # local build/push helper
├── .gitignore
└── .dockerignore
```

## Setup

1. Copy the env template and fill in real values:
   ```bash
   cp .env.example .env
   ```
   Fill in `PUREVPN_EMAIL`, `PUREVPN_PASSWORD`, and a **rotated** `TS_AUTHKEY`.
   `.env` is gitignored — never commit it.

2. Build locally to test:
   ```bash
   ./build.sh
   ```

3. Or let CI build it: push to `main` (or trigger the workflow manually) and
   it publishes to `ghcr.io/<your-user>/<your-repo>:latest`.

4. Bring up the stack:
   ```bash
   docker compose up -d
   ```

## How the watchdog works

- Every `CHECK_INTERVAL` seconds, checks `docker inspect`'s health status for
  the container named `TARGET_CONTAINER` (default `gluetun-exit`), via the
  Docker SDK talking to the mounted `/var/run/docker.sock`.
- After `UNHEALTHY_THRESHOLD` consecutive unhealthy checks, it runs
  `download_config.py` to fetch a new `wg0.conf` into the shared `./wireguard`
  volume, then restarts gluetun.
- After a fix attempt, it sleeps `COOLDOWN_AFTER_FIX` seconds before resuming
  checks, so it doesn't hammer PureVPN's login if something else is wrong.

## Why Xvfb instead of headless mode

PureVPN's dashboard (like some other sites) detects and stalls on a truly
headless Chromium. `entrypoint.sh` runs the whole process under `xvfb-run`,
which starts a virtual X display and sets `DISPLAY` for the shell; both
`watchdog.py` and the `download_config.py` subprocess it spawns inherit that,
so Chromium launched with `headless=False` renders to the virtual screen
instead of a real one.