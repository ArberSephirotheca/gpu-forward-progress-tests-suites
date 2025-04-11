docker buildx build --target generate-final --output type=local,dest=. .
sh ./test_amber/to_run.sh