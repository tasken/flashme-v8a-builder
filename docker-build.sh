#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ $EUID -eq 0 ]]; then
	echo "Run this as your normal user. It calls sudo for docker itself, so every output file stays yours." >&2
	exit 1
fi

# name:suffix pairs; the name is the VARIANT value passed to each package Makefile.
VARIANTS=("normal:" "stealth:_stealth" "noauto:_noauto" "stealth-noauto:_stealth_noauto")
PACKAGE_ROOT=/src/dscfw/flashme/v8a
LOG=logs/build.log

# docker compose reads these from .env, which survives sudo's environment reset.
sync_env() {
	local tmp
	tmp="$(mktemp)"
	{
		[[ -f .env ]] && grep -v -E '^BUILD_(UID|GID)=' .env || true
		printf 'BUILD_UID=%s\nBUILD_GID=%s\n' "$(id -u)" "$(id -g)"
	} > "$tmp"
	mv -- "$tmp" .env
}

compose() {
	sudo docker compose "$@" 2>&1 | tee -a "$LOG"
}

# Every input must exist and match tools/inputs.sha256 (see tools/check_inputs.py for the hash rules).
require_inputs() {
	local version file
	local -a files=()
	for version in "$@"; do
		files+=("official_${version}.bin")
	done
	files+=(flashme/FlashMe_v8a.zip)
	for file in "${files[@]}"; do
		if [[ ! -f "inputs/$file" ]]; then
			printf '%s\n' \
				"Missing inputs/$file." \
				"Firmware dumps and the FlashMe release are user-provided and are not downloaded or included in the image." >&2
			return 1
		fi
	done
	python3 tools/check_inputs.py "${files[@]}"
}

# build_package <package> <firmware> <image-name> <stored-crc16: yes|no>
build_package() {
	local package="$1" firmware="$2" name="$3" stored_crc="$4"
	local pair variant suffix
	local -a args

	for pair in "${VARIANTS[@]}"; do
		variant="${pair%%:*}"
		suffix="${pair#*:}"
		args=("VARIANT=$variant" pack
			"OUTPUT=/output/firmware/${name}${suffix}.bin"
			"OFFICIAL_${firmware^^}=/inputs/official_${firmware}.bin")
		if [[ $stored_crc == yes ]]; then
			args+=("CRC16_FILE=$PACKAGE_ROOT/$package/flashme_v8a_${package}${suffix}.crc16")
		fi
		compose run --rm builder make -C "$PACKAGE_ROOT/$package" "${args[@]}"
	done
}

clean() {
	rm -rf -- out/firmware out/installers logs/*.log
}

build_images() {
	local update="$1"
	if [[ $update == yes ]]; then
		require_inputs v5 v7
	else
		require_inputs v3 v6
	fi
	mkdir -p out/firmware out/installers logs
	: > "$LOG"
	sync_env

	compose build
	if [[ $update == yes ]]; then
		build_package phat_v5 v5 flashme_v8a_phat_v5 no
		build_package lite_v7 v7 flashme_v8a_lite_v7 no
		python3 tools/finalize.py --update 2>&1 | tee -a "$LOG"
	else
		build_package phat v3 flashme_v8a_phat_v3 yes
		build_package lite v6 flashme_v8a_lite_v6 yes
		python3 tools/finalize.py 2>&1 | tee -a "$LOG"
	fi
}

usage() {
	printf '%s\n' "Usage: ./docker-build.sh build [--update]" "       ./docker-build.sh clean" >&2
	exit 2
}

case "${1:-build}" in
	build)
		update=no
		case "${2:-}" in
			"") ;;
			--update) update=yes ;;
			*) usage ;;
		esac
		clean
		build_images "$update"
		;;
	clean)
		clean
		;;
	*)
		usage
		;;
esac
