FROM debian:stable-slim AS tools

ARG DSCFW_REF=87cab6c5f5093e8845601ce4619a61bb032977f6
ARG ARMIPS_REF=98757e2fdc79a21a1aeb884d05f4312125fffd68
ARG DSFWTOOL_REF=71eec8c41946a6df8fb10ed05e6812669e38513b

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

# The native dsfwtool supports --layout, so the Makefiles call it directly.
COPY --from=tools /usr/local/bin/dsfwtool-native /usr/local/libexec/dsfwtool-native
RUN ln -sf /usr/local/libexec/dsfwtool-native /src/dscfw/tools/dsfwtool/dsfwtool && \
    ln -sf /usr/local/libexec/dsfwtool-native /usr/local/bin/dsfwtool

USER builder
WORKDIR /src/dscfw
CMD ["dsfwtool", "--help"]
