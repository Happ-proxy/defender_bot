#!/usr/bin/env bash

set -euo pipefail

IMAGE_BASE="ghcr.io/jolymmiles/defender_bot"

read -rp "Enter release version (e.g. 1.0.0): " VERSION
if [[ -z "${VERSION}" ]]; then
  echo "Error: Version must not be empty" >&2
  exit 1
fi

MAJOR_VERSION="${VERSION%%.*}"
if [[ -z "${MAJOR_VERSION}" ]]; then
  echo "Error: Failed to derive major version from '${VERSION}'" >&2
  exit 1
fi

COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "none")

echo "Building and pushing Docker image..."
echo "Repository: ${IMAGE_BASE}"
echo "Version: ${VERSION}"
echo "Major version: ${MAJOR_VERSION}"
echo "Commit: ${COMMIT}"
echo ""

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg VERSION="${VERSION}" \
  --build-arg COMMIT="${COMMIT}" \
  -t "${IMAGE_BASE}:${VERSION}" \
  -t "${IMAGE_BASE}:${MAJOR_VERSION}" \
  -t "${IMAGE_BASE}:latest" \
  --push \
  .

echo ""
echo "✅ Successfully built and pushed Docker image!"
echo "Images:"
echo "  - ${IMAGE_BASE}:${VERSION}"
echo "  - ${IMAGE_BASE}:${MAJOR_VERSION}"
echo "  - ${IMAGE_BASE}:latest"
