import os
import subprocess
import sys
import time

import docker

TARGET_CONTAINER = os.environ.get("TARGET_CONTAINER", "gluetun-exit")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "30"))          # seconds between checks
UNHEALTHY_THRESHOLD = int(os.environ.get("UNHEALTHY_THRESHOLD", "3")) # consecutive unhealthy checks before acting
COOLDOWN_AFTER_FIX = int(os.environ.get("COOLDOWN_AFTER_FIX", "180")) # seconds to wait after a fix attempt before checking again

client = docker.from_env()


def get_health_status(container_name: str) -> str:
    """Returns 'healthy', 'unhealthy', 'starting', 'none' (no healthcheck), or 'missing'."""
    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound:
        return "missing"

    state = container.attrs.get("State", {})
    health = state.get("Health")
    if health is None:
        # No healthcheck defined - fall back to container running state
        return "healthy" if state.get("Status") == "running" else "unhealthy"
    return health.get("Status", "none")


def run_config_refresh() -> bool:
    print("[watchdog] Running config refresh script...", flush=True)
    result = subprocess.run(
        [sys.executable, "/app/download_config.py"],
        capture_output=True,
        text=True,
    )
    print(result.stdout, flush=True)
    if result.returncode != 0:
        print(f"[watchdog] Config refresh FAILED:\n{result.stderr}", file=sys.stderr, flush=True)
        return False
    print("[watchdog] Config refresh succeeded.", flush=True)
    return True


def restart_target():
    print(f"[watchdog] Restarting container '{TARGET_CONTAINER}'...", flush=True)
    try:
        container = client.containers.get(TARGET_CONTAINER)
        container.restart(timeout=30)
        print(f"[watchdog] '{TARGET_CONTAINER}' restarted.", flush=True)
    except docker.errors.NotFound:
        print(f"[watchdog] Container '{TARGET_CONTAINER}' not found, cannot restart.", file=sys.stderr, flush=True)


def main():
    print(
        f"[watchdog] Monitoring '{TARGET_CONTAINER}' every {CHECK_INTERVAL}s "
        f"(threshold: {UNHEALTHY_THRESHOLD} consecutive unhealthy checks)",
        flush=True,
    )
    consecutive_unhealthy = 0

    while True:
        status = get_health_status(TARGET_CONTAINER)
        print(f"[watchdog] '{TARGET_CONTAINER}' health: {status}", flush=True)

        if status == "unhealthy":
            consecutive_unhealthy += 1
        else:
            consecutive_unhealthy = 0

        if consecutive_unhealthy >= UNHEALTHY_THRESHOLD:
            print(f"[watchdog] '{TARGET_CONTAINER}' unhealthy {consecutive_unhealthy}x, attempting fix...", flush=True)
            consecutive_unhealthy = 0
            if run_config_refresh():
                restart_target()
                print(f"[watchdog] Cooling down for {COOLDOWN_AFTER_FIX}s before resuming checks...", flush=True)
                time.sleep(COOLDOWN_AFTER_FIX)
                continue
            else:
                print("[watchdog] Skipping restart since config refresh failed.", flush=True)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
