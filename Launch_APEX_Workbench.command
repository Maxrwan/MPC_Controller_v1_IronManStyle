#!/bin/zsh
# Double-click in Finder. Resolve paths from this file, not Terminal's working directory.
set -u
apex_workbench_root="${0:A:h}"
apex_workbench_python="$apex_workbench_root/tools/apex_workbench/.venv/bin/python"

if [[ ! -x "$apex_workbench_python" ]]; then
    print -r -- "Workbench setup is missing. Follow tools/apex_workbench/README.md first."
    read -r "apex_workbench_reply?Press Return to close. "
    exit 1
fi

"$apex_workbench_python" -I -S - "$apex_workbench_root" <<'PY'
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root = Path(sys.argv[1])
url = "http://127.0.0.1:8501"
try:
    with socket.socket() as available_port:
        available_port.bind(("127.0.0.1", 8501))
except OSError:
    print(f"Port 8501 is unavailable. An existing Workbench may already be open at {url}.")
    raise SystemExit(1)
print("Starting APEX Workbench. Your browser will open when it is ready.", flush=True)
print("Keep this Terminal window open. Press Control-C here to stop Workbench.", flush=True)
server = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", str(root / "tools/apex_workbench/app.py"),
     "--server.address", "127.0.0.1", "--server.port", "8501",
     "--server.headless", "true", "--browser.gatherUsageStats", "false"],
    cwd=root,
)
try:
    deadline = time.monotonic() + 30
    ready = False
    while time.monotonic() < deadline and server.poll() is None:
        try:
            with urllib.request.urlopen(url + "/_stcore/health", timeout=0.5) as response:
                ready = response.status == 200 and response.read().strip() == b"ok"
            if ready:
                # Detect a child that failed to bind while another server owns the port.
                time.sleep(0.3)
                if server.poll() is None:
                    subprocess.run(["/usr/bin/open", url], check=False)
                    break
                ready = False
        except OSError:
            pass
        time.sleep(0.1)
    if not ready:
        print("Workbench could not start. Check the messages above; port 8501 may be in use.")
        raise SystemExit(1)
    raise SystemExit(server.wait())
except KeyboardInterrupt:
    print("\nStopping Workbench.")
finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
PY
apex_workbench_status=$?
if (( apex_workbench_status != 0 )); then
    print -r -- "Launch failed. See the messages above or tools/apex_workbench/README.md."
    read -r "apex_workbench_reply?Press Return to close. "
fi
exit "$apex_workbench_status"
