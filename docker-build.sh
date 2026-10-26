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
ABOUT=no
FIRMWARE_ONLY=no
BUILT=()
PUBLIC=()

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

# Every named input must exist and match tools/inputs.sha256 (see tools/check_inputs.py for the hash rules).
require_inputs() {
	local file
	for file in "$@"; do
		if [[ ! -f "inputs/$file" ]]; then
			printf '%s\n' \
				"Missing inputs/$file." \
				"Firmware dumps and the FlashMe release are user-provided and are not downloaded or included in the image." >&2
			return 1
		fi
	done
	python3 tools/check_inputs.py "$@"
}

# Version shown by --about: short commit, "-dirty" with uncommitted changes or untracked files.
about_version() {
	local commit
	commit="$(git rev-parse --short=7 HEAD 2>/dev/null)" || { printf 'nogit'; return; }
	[[ -z "$(git status --porcelain 2>/dev/null)" ]] || commit+="-dirty"
	printf '%s' "$commit"
}

# build_package <package> <firmware> <image-name> <stored-crc16: yes|no>
build_package() {
	local package="$1" firmware="$2" name="$3" stored_crc="$4"
	local pair variant suffix
	local -a target args

	target=(pack)
	if [[ $ABOUT == yes ]]; then
		target=(-f Makefile -f ../include/about.mk about "ABOUT_FIRMWARE=${firmware#v}" "BUILD_VERSION=$(about_version)")
	fi
	for pair in "${VARIANTS[@]}"; do
		variant="${pair%%:*}"
		suffix="${pair#*:}"
		args=("VARIANT=$variant" "${target[@]}"
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

# plan_build <update: yes|no> sets BUILT (model:version pairs with a dump in inputs/) and PUBLIC (models that use the public image).
plan_build() {
	local update="$1" model version
	local -a files=()
	local -A versions=([phat]=v3 [lite]=v6)
	[[ $update == yes ]] && versions=([phat]=v5 [lite]=v7)

	BUILT=() PUBLIC=()
	for model in phat lite; do
		version="${versions[$model]}"
		if [[ -f "inputs/official_${version}.bin" ]]; then
			BUILT+=("$model:$version")
			files+=("official_${version}.bin")
		else
			PUBLIC+=("$model")
		fi
	done
	if [[ $update == yes && ${#BUILT[@]} -eq 0 ]]; then
		echo "--update needs inputs/official_v5.bin, inputs/official_v7.bin or both." >&2
		return 1
	fi
	if [[ $ABOUT == yes && ${#BUILT[@]} -eq 0 ]]; then
		echo "--about needs at least one firmware dump to build; every slot would come from the public release." >&2
		return 1
	fi
	if [[ $FIRMWARE_ONLY == no || ${#PUBLIC[@]} -gt 0 || -f inputs/flashme/FlashMe_v8a.zip ]]; then
		files+=(flashme/FlashMe_v8a.zip)
	fi
	require_inputs "${files[@]}"
}

# Raw images lack the console's own data, so --firmware-only asks before anything runs.
confirm_firmware_only() {
	local answer
	printf '%s\n' \
		"These firmware images are not complete. They have no MAC address, Wi-Fi" \
		"calibration, Wi-Fi settings or user settings. Never write them whole." \
		"" \
		"To flash one, use CFW-Suite fwManager (https://github.com/Wokann/CFW-Suite/releases/latest)" \
		"and keep its default \"Reserve old ...\" options, which keep your console's" \
		"own data. Do not choose \"Flash Complete Firmware\"." \
		"" >&2
	if [[ ! -t 0 ]]; then
		echo "--firmware-only needs a terminal to confirm. Nothing was built." >&2
		return 1
	fi
	read -r -p 'Type "yes" to confirm you understand: ' answer
	if [[ $answer != yes ]]; then
		echo "Not confirmed. Nothing was built." >&2
		return 1
	fi
}

build_images() {
	local update="$1" pair model version
	local -a finalize_args=()
	mkdir -p out/firmware logs
	: > "$LOG"

	if [[ ${#BUILT[@]} -gt 0 ]]; then
		sync_env
		compose build
	fi
	for pair in "${BUILT[@]}"; do
		model="${pair%%:*}"
		version="${pair#*:}"
		if [[ $update == yes ]]; then
			build_package "${model}_${version}" "$version" "flashme_v8a_${model}_${version}" no
		else
			build_package "$model" "$version" "flashme_v8a_${model}_${version}" yes
		fi
	done
	[[ $update == yes ]] && finalize_args+=(--update)
	[[ $ABOUT == yes ]] && finalize_args+=(--about)
	[[ $FIRMWARE_ONLY == yes ]] && finalize_args+=(--firmware-only)
	python3 tools/finalize.py "${finalize_args[@]}" 2>&1 | tee -a "$LOG"
	python3 tools/fresh_settings.py out/firmware/*.bin 2>&1 | tee -a "$LOG"
}

usage() {
	printf '%s\n' "Usage: ./docker-build.sh build [--update] [--about] [--firmware-only]" "       ./docker-build.sh clean" >&2
	exit 2
}

case "${1:-build}" in
	build)
		update=no
		for option in "${@:2}"; do
			case "$option" in
				--update) update=yes ;;
				--about) ABOUT=yes ;;
				--firmware-only) FIRMWARE_ONLY=yes ;;
				*) usage ;;
			esac
		done
		plan_build "$update"
		[[ $FIRMWARE_ONLY == yes ]] && confirm_firmware_only
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
