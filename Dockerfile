FROM debian:stable-slim AS tools

ARG DSCFW_REF=7389c00230cdc494353916bb5742573efbf58a0f
ARG ARMIPS_REF=98757e2fdc79a21a1aeb884d05f4312125fffd68
ARG DSFWTOOL_REF=b25dafbe7483037fc373bb8e7bb920778ed49d0a

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Wokann/dscfw.git /src/dscfw && \
    git -C /src/dscfw checkout --detach "${DSCFW_REF}" && \
    git clone --recurse-submodules --branch flashme-arm-immediate-encoding \
      --single-branch https://github.com/Wokann/armips.git /tmp/armips && \
    git -C /tmp/armips checkout --detach "${ARMIPS_REF}" && \
    cmake -S /tmp/armips -B /tmp/armips-build \
      -DCMAKE_BUILD_TYPE=Release \
      -DARMIPS_USE_STD_FILESYSTEM=ON && \
    cmake --build /tmp/armips-build --target armips-bin --parallel && \
    cmake --install /tmp/armips-build --prefix /usr/local && \
    install -D -m 0755 /usr/local/armips /src/dscfw/tools/armips/armips && \
    git clone https://github.com/Wokann/dsfwtool.git /tmp/dsfwtool && \
    git -C /tmp/dsfwtool checkout --detach "${DSFWTOOL_REF}" && \
    make -C /tmp/dsfwtool dsfwtool && \
    install -m 0755 /tmp/dsfwtool/release/dsfwtool /usr/local/bin/dsfwtool-native && \
    make -C /src/dscfw/tools/crc && \
    rm -rf /src/dscfw/.git /tmp/armips /tmp/armips-build /tmp/dsfwtool

FROM debian:stable-slim

ARG BUILD_UID=1000
ARG BUILD_GID=1000

# Builds run as an unprivileged user whose ids match the host user, so every
# file written to the mounted out/ folder belongs to you, not root.
RUN test "${BUILD_UID}" != 0 && test "${BUILD_GID}" != 0 && \
    apt-get update && apt-get install -y --no-install-recommends \
    make python3 \
    && rm -rf /var/lib/apt/lists/* && \
    groupadd --non-unique --gid "${BUILD_GID}" builder && \
    useradd --non-unique --uid "${BUILD_UID}" --gid "${BUILD_GID}" \
      --create-home --shell /usr/sbin/nologin builder

COPY --from=tools --chown=builder:builder /src/dscfw /src/dscfw
COPY --chown=builder:builder packages/ /src/dscfw/flashme/v8a/

# The native dsfwtool lacks --layout; the wrapper accepts dscfw's Makefile command lines
# (see tools/dsfwtool_wrapper.py) and packs byte for byte like the dsfwtool.exe shipped in dscfw.
COPY --from=tools /usr/local/bin/dsfwtool-native /usr/local/libexec/dsfwtool-native
COPY --chown=builder:builder tools/dsfwtool_wrapper.py /src/dscfw/tools/dsfwtool/dsfwtool
RUN chmod 0755 /src/dscfw/tools/dsfwtool/dsfwtool && \
    ln -s /src/dscfw/tools/dsfwtool/dsfwtool /usr/local/bin/dsfwtool

USER builder
WORKDIR /src/dscfw
CMD ["dsfwtool", "--help"]
