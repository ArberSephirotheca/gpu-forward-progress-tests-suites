#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status
sh ./generate.sh

# Run the test script
(
    cd ./test_amber 
    sh ./to_run.sh
)

