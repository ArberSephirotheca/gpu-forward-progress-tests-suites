#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF >&2
Usage: $0 -g GPU_NAME [-a 1] [-s SERIAL] [-d DEVICE]
  -g   GPU name (to be used in table of results)
  -a   run Android tests with adb
  -s   device serial (only valid with -a)
  -d   device name/ID for non-Android tests
EOF
  exit 1
}

# default values
test="core"
android=""
serial=""
device=""

# parse options
while getopts ":g:t:a:s:d:h:" opt; do
  case $opt in
    g) gpu_name=$OPTARG ;;
    t) test=$OPTARG ;;
    a) android=$OPTARG ;;
    s) serial=$OPTARG ;;
    d) device=$OPTARG ;;
    h) usage ;;
    :) echo "Error: option -${OPTARG} requires an argument." >&2; usage ;;
    \?) echo "Error: invalid option -${OPTARG}" >&2; usage ;;
  esac
done

if [[ -z "${gpu_name:-}" ]]; then
  echo "Error: GPU name is required (-g)." >&2
  usage
fi

# build up the command
cmd=(python3 amber_launch_tests.py "$test" --gpu "$gpu_name")

if [[ -n $android ]]; then
  cmd+=(--android)
  if [[ -n $serial ]]; then
    cmd+=(--serial "$serial")
  fi
elif [[ -n $device ]]; then
  cmd+=(--device "$device")
fi

# run it once
"${cmd[@]}"

bash cleanup.sh
python3 summarize.py