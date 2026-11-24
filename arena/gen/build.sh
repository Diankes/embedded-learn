#!/usr/bin/env bash
# Regenerate arena/puzzles.json. Run on the host (needs podman, the `embedded` box's toolchain and ESP-IDF, and
# chip-canvas's text copies of the TRM and specs). Everything is mounted read-only; only arena/ is written.
#   arena/gen/build.sh
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
esp="$HOME/.local/share/bench/embedded/.espressif"
tc=$(find "$esp/tools/riscv32-esp-elf" -mindepth 2 -maxdepth 2 -type d -name riscv32-esp-elf | sort | tail -1)   # bin/ + libexec/
idf="$esp/v6.1/esp-idf"
text="$HOME/projects/chip-canvas/sources/text"
for d in "$tc" "$idf" "$text"; do [[ -d $d ]] || { echo "missing: $d" >&2; exit 1; }; done

podman build -q -t localhost/arena-gen -f "$here/Containerfile" "$here" >/dev/null
podman run --rm --security-opt label=disable \
  -v "$tc:/tc:ro" -v "$idf:/idf:ro" -v "$text:/text:ro" -v "$here:/gen:ro" -v "$here/..:/out" \
  localhost/arena-gen python3 -I /gen/gen.py
