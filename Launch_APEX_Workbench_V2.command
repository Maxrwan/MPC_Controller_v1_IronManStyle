#!/bin/zsh
# V2 has its own entrypoint/port; accepted V1's launcher and files are unchanged.
set -u
apex_lap_root="${0:A:h}"
apex_lap_env="$apex_lap_root/tools/apex_workbench/.venv"
apex_lap_python="${apex_lap_env:A}/bin/python"
if [[ ! -x "$apex_lap_python" ]]; then
    print -r -- "Workbench environment missing. See tools/apex_workbench/README.md."
    exit 1
fi
cd "$apex_lap_root" || exit 1
exec "$apex_lap_python" -B -m tools.apex_workbench.lap.launch
