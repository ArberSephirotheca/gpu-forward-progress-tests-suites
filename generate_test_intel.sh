#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Build the Docker image and generate output locally
docker buildx build --target generate-final-intel --output type=local,dest=. .

# Run the test script
(
    cd ./test_amber 
    sh ./to_run_intel.sh
    python3 summarize.py)