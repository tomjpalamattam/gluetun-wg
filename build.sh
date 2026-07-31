#!/bin/bash
# Local build (and optional push) helper, mirrors what the GitHub Actions
# workflow does, for testing before you push to main.
#
# Usage:
#   ./build.sh                 # build only, tag as local/gluetun-config-refresher:latest
#   ./build.sh push ghcr.io/<user>/<repo>   # build AND push to that image ref
set -euo pipefail

LOCAL_TAG="local/gluetun-config-refresher:latest"

echo "Building image: $LOCAL_TAG"
docker build -t "$LOCAL_TAG" .

if [[ "${1:-}" == "push" ]]; then
    REMOTE_REF="${2:?Usage: ./build.sh push <registry>/<image-name>}"
    echo "Tagging as $REMOTE_REF:latest"
    docker tag "$LOCAL_TAG" "$REMOTE_REF:latest"
    echo "Pushing $REMOTE_REF:latest (make sure you've run 'docker login ghcr.io' first)"
    docker push "$REMOTE_REF:latest"
fi

echo "Done."
