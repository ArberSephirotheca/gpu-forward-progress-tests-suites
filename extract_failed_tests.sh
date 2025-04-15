#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Run the test script
(
    cd ./test_amber 
    python3 extract_failed_tests.py
)
# Build the Docker image and generate output locally
docker buildx build --target reduce-final --output type=local,dest=. .

