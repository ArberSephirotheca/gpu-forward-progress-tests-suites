set -e
rm -rf all_tests
rm -rf all_tests_fixed_subgroup
mkdir -p "$(pwd)/all_tests"
mkdir -p "$(pwd)/all_tests_fixed_subgroup"
# docker buildx build --target generate .
# docker buildx build \
#   --target generate \
#   --output "type=local,src=/opt/graphicsfuzz/temp/output,dest=./all_tests" \
#   .
DOCKER_BUILDKIT=1 docker buildx build \
  --load \
  --build-arg HOST_UID="$(id -u)" \
  --build-arg HOST_GID="$(id -g)" \
  --target generate \
  -t glsl-generator:local \
  .
docker run --rm \
  -v "$(pwd)/references:/opt/graphicsfuzz/temp/references" \
  -v "$(pwd)/donors:/opt/graphicsfuzz/temp/donors" \
  -v "$(pwd)/all_tests:/opt/graphicsfuzz/temp/output" \
  glsl-generator:local
python3 replace_all_sub_group_size.py
