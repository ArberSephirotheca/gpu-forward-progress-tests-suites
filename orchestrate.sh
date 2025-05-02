#!/usr/bin/env bash
set -euo pipefail   # exit on error, undefined var, or pipe failure

##############################################################################
#  Helpers
##############################################################################

# Prepare references directory for mounting into the container.
#   $1 = pipeline  (core | generic)
#   $2 = test dir  (may be empty)
_prepare_ref_mount() {
  local pipeline=$1 test=$2 base host_dir

  # Pick the right base tree
  if [[ $pipeline == core ]]; then
    base="references_core"
  else
    base="references"
  fi

  if [[ -n $test ]]; then                            # single sub-dir mount
    host_dir="$(pwd)/${base}/${test}"
  else                                               # maybe flatten nested refs
    if find "${base}" -mindepth 2 -type f \( -name '*.comp' -o -name '*.json' \) \
           | read -r _; then
      host_dir=$(mktemp -d)
      find "${base}" -type f \( -name '*.comp' -o -name '*.json' \) \
           -exec cp {} "${host_dir}/" \;
    else
      host_dir="$(pwd)/${base}"
    fi
  fi
  echo "${host_dir}:/opt/graphicsfuzz/temp/references"
}

##############################################################################
#  Generation
##############################################################################

gen_core() {
  local test=${1:-}
  echo "==> [Generate → core] dir='${test:-all}'"
  mkdir -p all_tests_core

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
}

gen() {
  local test=${1:-}
  echo "==> [Generate → core] dir='${test:-all}'"
  mkdir -p all_tests

  DOCKER_BUILDKIT=1 docker buildx build \
    --load \
    --build-arg HOST_UID="$(id -u)" \
    --build-arg HOST_GID="$(id -g)" \
    --target generate \
    -t glsl-generator:local .

  docker run --rm \
    -v "$(_prepare_ref_mount "$test")" \
    -v "$(pwd)/donors:/opt/graphicsfuzz/temp/donors" \
    -v "$(pwd)/all_tests:/opt/graphicsfuzz/temp/output" \
    glsl-generator:local
}

gen_generic() { echo "==> [Generate → generic]"; gen "$1"; }

##############################################################################
#  Run helpers
##############################################################################

_run_common() {
  local suite=$1         # core | generic
  local args=(-t "$suite")
  $ANDROID        && args+=(-a "1")
  [[ -n $SERIAL ]] && args+=(-s "$SERIAL")
  [[ -n $DEVICE ]] && args+=(-d "$DEVICE")
  ( cd test_amber && ./to_run.sh "${args[@]}" )
}

run_core()       { _run_common core        ; }
run_generic()    { _run_common generic     ; }

##############################################################################
#  Usage (includes examples)
##############################################################################

usage() {
  cat <<'EOF'
Usage: orchestrate.sh <action> <pipeline> [dir] [flags]

  action:
    generate   generate shaders only
    run        run tests only
    both       generate then run
    help       print this message

  pipeline:
    core | generic

  dir (optional):
    Sub-directory under references[_core] to limit generation. If omitted, all
    reference shaders are used (nested sub-dirs are flattened automatically).

  flags (valid for "run" or "both"):
    -a, --android           run on Android via adb
    -s, --serial SERIAL     adb serial (use when multiple phones are plugged in)
    -d, --device  ID        Vulkan device index on host or Android target

Examples
========
  # 1. Generate core shaders and run on host default GPU
  ./orchestrate.sh both core

  # 2. Generate core shaders for sub-dir "my_case" only
  ./orchestrate.sh generate core my_case

  # 3. Run existing generic tests on host GPU 1
  ./orchestrate.sh run generic -d 1

  # 4. Run core suite on first Android device adb sees
  ./orchestrate.sh run core -a

  # 5. Run core on a specific phone and force Vulkan device 0 inside it
  ./orchestrate.sh run core -a -s 0123456789ABCDEF -d 0
EOF
}

##############################################################################
#  Parse positional action + pipeline
##############################################################################

[[ $# -eq 0 || $1 == help ]] && { usage; exit 0; }

ACTION=$1
PIPELINE=$2
shift 2                    # leave the rest for [dir] and/or flags

##############################################################################
#  Parse optional dir and flags
##############################################################################

DIR=""
ANDROID=false
SERIAL=""
DEVICE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -a|--android) ANDROID=true ;;
    -s|--serial)  SERIAL=$2; shift ;;
    -d|--device)  DEVICE=$2; shift ;;
    *)            DIR=$1 ;;
  esac
  shift
done

##############################################################################
#  Dispatch
##############################################################################

case $ACTION in
  generate)
    case $PIPELINE in
      core)        gen_core "$DIR" ;;
      generic)     gen_generic "$DIR" ;;
      *) echo "Unknown pipeline: $PIPELINE" ; usage ; exit 1 ;;
    esac ;;
  run)
    case $PIPELINE in
      core)        run_core ;;
      generic)     run_generic ;;
      *) echo "Unknown pipeline: $PIPELINE" ; usage ; exit 1 ;;
    esac ;;
  both)
    case $PIPELINE in
      core)        gen_core "$DIR"       ; run_core ;;
      generic)     gen_generic "$DIR"    ; run_generic ;;
      *) echo "Unknown pipeline: $PIPELINE" ; usage ; exit 1 ;;
    esac ;;
  *)
    echo "Unknown action: $ACTION"
    usage
    exit 1 ;;
esac
