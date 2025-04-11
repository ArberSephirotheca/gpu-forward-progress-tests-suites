#! to execute: 
    # install docker buildx if not installed
    # docker buildx build --target final --output type=local,dest=./output .
FROM ubuntu:22.04 AS builder 

# Install essential packages
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    openjdk-11-jdk \
    python3 \
    vim \
    python3-pip \
    git \
    wget \
    unzip \
    maven \
    cmake \
    build-essential \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install pipenv globally
RUN pip3 install --upgrade pip && pip3 install pipenv mako types-requests types-python-dateutil

# Install GraphicsFuzzs
WORKDIR /opt
RUN git clone https://github.com/ArberSephirotheca/graphicsfuzz.git && \
    cd graphicsfuzz && \
    git submodule update --init && \
    mvn package -e -DskipTests=true
# COPY . /opt/graphicsfuzz
# RUN cd graphicsfuzz && \
#     git submodule update --init && \
#     mvn package -e -DskipTests=true

# WORKDIR /opt
# COPY ./glslang /opt/glslang
# RUN cd glslang && \
#     ./update_glslang_sources.py && \
#     mkdir -p build && \
#     cd build && \
#     cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$(pwd)/install" .. && \
#     make -j4 install

# RUN cp /opt/glslang/build/install/bin/* /opt/graphicsfuzz/graphicsfuzz/target/graphicsfuzz/bin/Linux
ENV PATH="/opt/graphicsfuzz/graphicsfuzz/target/graphicsfuzz/bin/Linux:${PATH}"
ENV PATH="/opt/graphicsfuzz/graphicsfuzz/target/graphicsfuzz/python/drivers:${PATH}"

FROM builder AS generate
WORKDIR /opt/graphicsfuzz/temp
COPY references /opt/graphicsfuzz/temp/references
COPY fake_donors /opt/graphicsfuzz/temp/donors
RUN glsl-generate --vulkan ./references ./donors 100 syn /output

FROM builder AS generate-intel
WORKDIR /opt/graphicsfuzz/temp
COPY references_intel_fix_subgroup /opt/graphicsfuzz/temp/references
COPY fake_donors /opt/graphicsfuzz/temp/donors
RUN glsl-generate --vulkan ./references ./donors 100 syn /output

FROM scratch AS generate-final
COPY --from=generate /output all_tests


FROM scratch AS generate-final-intel
COPY --from=generate /output all_tests_intel

FROM builder AS reduce
WORKDIR /opt
COPY test_suite/all_tests/syn_branch_syn_release/variant_034.comp /opt/reduce/reduce.comp
COPY test_suite/all_tests/syn_branch_syn_release/variant_034.json /opt/reduce/reduce.json
COPY graphicsfuzz/src/main/scripts/examples/glsl-reduce-walkthrough /opt/reduce/examples
ENV PATH="/opt/reduce:${PATH}"
RUN glsl-reduce /opt/reduce/reduce.json interestingness_test --output reduction_results

FROM scratch AS reduce-final
COPY --from=reduce /opt/reduction_results test_suite/all_tests

