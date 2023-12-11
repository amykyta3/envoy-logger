#!/usr/bin/env bash
set -eou pipefail

image_name=maniacmog/envoy-logger
image_and_tags=()
docker_build_tags=()

push=0
while getopts "p" arg; do
  case $arg in
    p) push=1;;
    *) exit 1;;
  esac
done
shift "$((OPTIND-1))"

# Add tags from parameters
for tag in "${@}"; do
  image="${image_name}:${tag}"
  image_and_tags+=("${image}")
  docker_build_tags+=('-t' "${image}")
done

if (( ${#docker_build_tags[@]} > 0 )); then
  # Build image with all tags
  echo "Building ${image_and_tags[*]}"
  docker build "${docker_build_tags[@]}" .

  # Push each tag
  if [ ${push} == 1 ]; then
    echo "Pushing ${image_and_tags[*]}"
    for image in "${image_and_tags[@]}"; do
      docker push "${image}"
    done
  else
    echo 'Skipping docker push'
  fi
fi
