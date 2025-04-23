#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF >&2
Usage: $0 [-a ANDROID_PATH] [-s SERIAL] [-d DEVICE]
  -a   path to Android sdk/emulator
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
while getopts ":t:a:s:d:h:" opt; do
  case $opt in
    t) test=$OPTARG ;;
    a) android=$OPTARG ;;
    s) serial=$OPTARG ;;
    d) device=$OPTARG ;;
    h) usage ;;
    :) echo "Error: option -${OPTARG} requires an argument." >&2; usage ;;
    \?) echo "Error: invalid option -${OPTARG}" >&2; usage ;;
  esac
done


# build up the command
cmd=(python3 amber_launch_tests.py $test)

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