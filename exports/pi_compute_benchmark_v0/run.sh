#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IMAGE=apex-pi-compute:v0
mkdir -p "$ROOT/results"
RUN_DIR=$(mktemp -d "$ROOT/results/run-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
{
    date -u
    uname -a
    cat /etc/os-release 2>/dev/null || true
    cat /proc/device-tree/model 2>/dev/null || true
    cat /proc/cpuinfo 2>/dev/null || true
    command -v lscpu >/dev/null 2>&1 && lscpu || true
    for value in /sys/class/thermal/thermal_zone*/temp /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        [ ! -r "$value" ] || { printf '\n%s\n' "$value"; cat "$value"; }
    done
    if command -v vcgencmd >/dev/null 2>&1; then
        vcgencmd measure_temp || true
        vcgencmd get_throttled || true
    else
        printf '\nvcgencmd unavailable; throttling status unknown\n'
    fi
    docker image inspect "$IMAGE" --format 'image_id={{.Id}} platform={{.Os}}/{{.Architecture}}'
} > "$RUN_DIR/host.txt" 2>&1
printf 'Results: %s\n' "$RUN_DIR"
if docker run --rm --init --platform linux/arm64 --network none --read-only \
    --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$ROOT/results,dst=/opt/benchmark/results" \
    "$IMAGE" --output "results/$(basename "$RUN_DIR")" "$@"; then
    STATUS=0
else
    STATUS=$?
fi
{
    printf '\nAfter benchmark (read-only host observations):\n'
    date -u
    if command -v vcgencmd >/dev/null 2>&1; then
        vcgencmd measure_temp || true
        vcgencmd get_throttled || true
    fi
} >> "$RUN_DIR/host.txt" 2>&1
exit "$STATUS"
