#!/bin/bash
set -e  # Exit on any error

# —— Helpers ——

# Prepare references directory for mounting into the container.
# If a specific subdir is given, mount that. Otherwise, if the base
# references directory contains nested subdirectories with .comp/.json,
# flatten them into a temp dir so the generator can see all files.
_prepare_ref_mount() {
  local pipeline=$1 test=$2
  local base
  # Choose between references_core and references
  if [[ $pipeline == core || $pipeline == intel-core ]]; then
    base="references_core"
  else
    base="references"
  fi

  local host_dir
  if [[ -n "$test" ]]; then
    # Mount only that subdirectory
    host_dir="$(pwd)/${base}/${test}"
  else
    # No specific test: detect nested .comp/.json files
    if find "${base}" -mindepth 2 -type f \( -name '*.comp' -o -name '*.json' \) | read; then
      host_dir=$(mktemp -d)
      find "${base}" -type f \( -name '*.comp' -o -name '*.json' \) -exec cp {} "${host_dir}/" \;
    else
      host_dir="$(pwd)/${base}"
    fi
  fi
  echo "${host_dir}:/opt/graphicsfuzz/temp/references"
}

# —— Generation functions ——

gen_core() {
  local test=$1
  echo "==> [Generate → Core] dir='${test:-all}'"
  mkdir -p all_tests_core all_tests_fixed_subgroup

  DOCKER_BUILDKIT=1 docker buildx build \
    --load \
    --build-arg HOST_UID="$(id -u)" \
    --build-arg HOST_GID="$(id -g)" \
    --target generate-core \
    -t glsl-generator-core:local .

  docker run --rm \
    -v "$(_prepare_ref_mount core "$test")" \
    -v "$(pwd)/donors:/opt/graphicsfuzz/temp/donors" \
    -v "$(pwd)/all_tests_core:/opt/graphicsfuzz/temp/output" \
    glsl-generator-core:local

  python3 replace_all_sub_group_size.py core
}

gen_intel_core() {
  echo "==> [Generate → Intel‑Core] dir='${1:-all}'"
  gen_core "$1"
}

gen_intel() {
  local test=$1
  echo "==> [Generate → Intel] dir='${test:-all}'"
  mkdir -p all_tests all_tests_fixed_subgroup

  DOCKER_BUILDKIT=1 docker buildx build \
    --load \
    --build-arg HOST_UID="$(id -u)" \
    --build-arg HOST_GID="$(id -g)" \
    --target generate \
    -t glsl-generator:local .

  docker run --rm \
    -v "$(_prepare_ref_mount intel "$test")" \
    -v "$(pwd)/donors:/opt/graphicsfuzz/temp/donors" \
    -v "$(pwd)/all_tests:/opt/graphicsfuzz/temp/output" \
    glsl-generator:local

  python3 replace_all_sub_group_size.py
}

gen_generic() {
  echo "==> [Generate → Generic] dir='${1:-all}'"
  gen_intel "$1"
}

# —— Run functions ——

run_core() {
  echo "==> [Run → Core]"
  (cd test_amber && sh to_run_core.sh)
}

run_intel_core() {
  echo "==> [Run → Intel‑Core]"
  (cd test_amber && sh to_run_intel_core.sh)
}

run_intel() {
  echo "==> [Run → Intel]"
  (cd test_amber && sh to_run_intel.sh)
}

run_generic() {
  echo "==> [Run → Generic]"
  (cd test_amber && sh to_run.sh)
}

# —— Usage message ——

usage() {
  cat <<EOF
Usage: $0 <action> <pipeline> [dir]
  action:
    generate — only generate (optionally for one subdirectory under references[_core])
    run      — only run tests
    both     — generate then run
    help     — this message

  pipeline:
    core, intel-core, intel, generic

  [dir]:
    subdirectory name under references or references_core (no extensions)
    if omitted, scripts will detect nested .comp/.json files and flatten them
EOF
}

# —— Dispatch ——

if [[ $# -eq 0 || $1 == help ]]; then
  usage; exit
fi

ACTION=$1
PIPE=$2
DIR=${3:-}

case $ACTION in
  generate)
    case $PIPE in
      core)        gen_core      "$DIR" ;;  
      intel-core)  gen_intel_core "$DIR" ;;  
      intel)       gen_intel     "$DIR" ;;  
      generic)     gen_generic   "$DIR" ;;  
      *)           echo "Unknown pipeline: $PIPE"; usage; exit 1 ;;  
    esac
    ;;
  run)
    case $PIPE in
      core)        run_core       ;;  
      intel-core)  run_intel_core ;;  
      intel)       run_intel      ;;  
      generic)     run_generic    ;;  
      *)           echo "Unknown pipeline: $PIPE"; usage; exit 1 ;;  
    esac
    ;;
  both)
    case $PIPE in
      core)
        gen_core "$DIR"
        run_core
        ;;  
      intel-core)
        gen_intel_core "$DIR"
        run_intel_core
        ;;  
      intel)
        gen_intel "$DIR"
        run_intel
        ;;  
      generic)
        gen_generic "$DIR"
        run_generic
        ;;  
      *) echo "Unknown pipeline: $PIPE"; usage; exit 1 ;;  
    esac
    ;;
  *)
    echo "Unknown action: $ACTION"; usage; exit 1
    ;;
esac
