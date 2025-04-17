#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status
rm -rf ./failed_variants
# Run the test script
(
    cd ./test_amber 
    python3 extract_failed_variants.py
)
# Remove previously created local reduction_results and failed variants
rm -rf ./reduction_results
# Build the Docker image and generate output locally
docker buildx build --target reduce-final --output type=local,dest=. .

