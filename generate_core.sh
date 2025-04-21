set -e
# rm -rf all_tests
# rm -rf all_tests_fixed_subgroup
mkdir -p "$(pwd)/all_tests"
mkdir -p "$(pwd)/all_tests_fixed_subgroup"

DOCKER_BUILDKIT=1 docker buildx build \
  --load \
  --build-arg HOST_UID="$(id -u)" \
  --build-arg HOST_GID="$(id -g)" \
  --target generate-core \
  -t glsl-generator-core:local \
  .
docker run --rm \
  -v "$(pwd)/references_core:/opt/graphicsfuzz/temp/references" \
  -v "$(pwd)/donors:/opt/graphicsfuzz/temp/donors" \
  -v "$(pwd)/all_tests_core:/opt/graphicsfuzz/temp/output" \
  glsl-generator-core:local
python3 replace_all_sub_group_size.py
