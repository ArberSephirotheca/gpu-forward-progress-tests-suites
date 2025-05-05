#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF >&2
Usage: $0 -g GPU_NAME [-t SUITE] [-a 1] [-s SERIAL] [-d DEVICE] [--dir DIR]
  -g   GPU name (used in results table) [required]
  -t   Test suite: core or generic [default: core]
  -a   Run on Android via adb
  -s   Android device serial (used with -a)
  -d   Vulkan device ID (host or Android)
  --dir  Subdirectory of test suite to run (optional)
EOF
  exit 1
}

# default values
test="core"
android=""
serial=""
device=""
dir=""

# parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -g) gpu_name="$2"; shift ;;
    -t) test="$2"; shift ;;
    -a) android=1 ;;
    -s) serial="$2"; shift ;;
    -d) device="$2"; shift ;;
    --dir) dir="$2"; shift ;;
    -h|--help) usage ;;
    *) echo "Error: Unknown argument: $1" >&2; usage ;;
  esac
  shift
done

if [[ -z "${gpu_name:-}" ]]; then
  echo "Error: GPU name is required (-g)." >&2
  usage
fi

# build command
cmd=(python3 amber_launch_tests.py "$test" --gpu "$gpu_name")

[[ -n $android ]] && cmd+=(--android)
[[ -n $serial ]] && cmd+=(--serial "$serial")
[[ -n $device ]] && cmd+=(--device "$device")
[[ -n $dir ]] && cmd+=(--dir "$dir")

# run
echo "Running: ${cmd[*]}"
"${cmd[@]}"

# post-processing
bash cleanup.sh
python3 summarize.py
