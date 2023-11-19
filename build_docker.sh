#!/usr/bin/env /bin/bash
set -xeou pipefail

image_name=maniacmog/envoy-logger
image_and_tags=()
docker_build_tags=()

# Add tags from parameters
for tag in "${@}"; do
  image="${image_name}:${tag}"
  image_and_tags+=("${image}")
  docker_build_tags+=('-t' "${image}")
done

if (( ${#docker_build_tags[@]} > 0 )); then
  # Build image with all tags
  docker build "${docker_build_tags[@]}" .

  # Push each tag
  for image in "${image_and_tags[@]}"; do
    docker push "${image}"
  done
fi
