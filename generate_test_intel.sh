docker buildx build --target generate-final-intel --output type=local,dest=. .
sh ./test_amber/to_run_intel.sh