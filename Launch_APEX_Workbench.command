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

"$apex_workbench_python" -I - "$apex_workbench_root" <<'PY'
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

try:
    import psutil
except ImportError:
    print("Workbench dependencies are missing. Follow tools/apex_workbench/README.md.")
    raise SystemExit(1)


def matching_server(root, port):
    """Resolve the actual listener; a generic Streamlit health response is insufficient."""
    try:
        result = subprocess.run(
            ["/usr/sbin/lsof", "-nP", f"-iTCP@127.0.0.1:{port}", "-sTCP:LISTEN", "-Fp"],
            capture_output=True, text=True, timeout=2,
        )
        pids = {int(line[1:]) for line in result.stdout.splitlines()
                if line.startswith("p") and line[1:].isdigit()}
        if len(pids) != 1:
            return None
        process = psutil.Process(pids.pop())
        command = process.cmdline()
        working = Path(process.cwd()).resolve()
        if (process.uids().real != os.getuid() or working != root
                or command[1:4] != ["-m", "streamlit", "run"] or len(command) < 5):
            return None
        app = Path(command[4])
        if not app.is_absolute():
            app = working / app
        if app.resolve() == root / "tools/apex_workbench/app.py" and process.is_running():
            return process
    except (OSError, ValueError, psutil.Error, subprocess.TimeoutExpired):
        pass
    return None


def healthy(url):
    try:
        # Loopback readiness must not depend on proxy environment variables.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url + "/_stcore/health", timeout=0.5) as response:
            return response.status == 200 and response.read().strip() == b"ok"
    except OSError:
        return False


def open_browser(url):
    if subprocess.run(["/usr/bin/open", url], check=False).returncode:
        print(f"Open {url} in your browser.", flush=True)


def launch(root, port=8501):
    root = Path(root).resolve()
    url = f"http://127.0.0.1:{port}"
    existing = matching_server(root, port)
    if existing is not None:
        deadline = time.monotonic() + 30
        while existing.is_running() and time.monotonic() < deadline:
            if healthy(url) and matching_server(root, port) is not None:
                print("Workbench is already running. Opening your browser.", flush=True)
                open_browser(url)
                return 0
            time.sleep(0.1)
        print("The existing Workbench is not responding. Check its Terminal window.")
        return 1
    try:
        with socket.socket() as available:
            available.bind(("127.0.0.1", port))
    except OSError:
        print(f"Port {port} is occupied by another application. Workbench could not start.")
        return 1
    print("Starting APEX Workbench from this project. Your browser will open when ready.", flush=True)
    print("Keep this Terminal window open. Press Control-C here to stop Workbench.", flush=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(root / "tools/apex_workbench/app.py"),
         "--server.address", "127.0.0.1", "--server.port", str(port),
         "--server.headless", "true", "--browser.gatherUsageStats", "false"], cwd=root,
    )
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and server.poll() is None:
            listener = matching_server(root, port) if healthy(url) else None
            if listener is not None and listener.pid == server.pid:
                open_browser(url)
                return server.wait()
            time.sleep(0.1)
        print("Workbench could not start. Check the messages above.")
        return 1
    except KeyboardInterrupt:
        print("\nStopping Workbench.")
        return 0
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


if __name__ == "__main__":
    try:
        raise SystemExit(launch(Path(sys.argv[1])))
    except KeyboardInterrupt:
        print("\nLaunch cancelled.")
        raise SystemExit(0)

PY
apex_workbench_status=$?
if (( apex_workbench_status != 0 )); then
    print -r -- "Launch failed. See the messages above or tools/apex_workbench/README.md."
    read -r "apex_workbench_reply?Press Return to close. "
fi
exit "$apex_workbench_status"
