"""Bounded review of the exact launcher; no launcher/product changes."""

import hashlib
import json
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import psutil

root, evidence = map(Path, sys.argv[1:])
launcher = root / "Launch_APEX_Workbench.command"
pin = "219b9358409fa73fc59f24a7755da66771883e6b"
assert launcher.read_bytes() == subprocess.check_output(
    ["git", "show", pin + ":Launch_APEX_Workbench.command"], cwd=root
)
with socket.socket() as available:
    available.bind(("127.0.0.1", 8501))
result = {
    "reviewed_sha": pin,
    "cwd": "/private/tmp",
    "launcher_sha256": hashlib.sha256(launcher.read_bytes()).hexdigest(),
}
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
helper = server = None
with (evidence / "launcher-server.log").open("x") as log:
    process = subprocess.Popen(
        [str(launcher)],
        cwd="/private/tmp",
        stdin=subprocess.PIPE,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    launch_process = psutil.Process(process.pid)
    launch_birth = launch_process.create_time()
    try:
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Launcher exited before ready")
            children = launch_process.children(recursive=True)
            for child in children:
                command = child.cmdline()
                if (
                    "-m" in command
                    and "streamlit" in command
                    and str(root / "tools/apex_workbench/app.py") in command
                ):
                    server = child
                if command[1:] == ["-I", "-S", "-", str(root)]:
                    helper = child
            try:
                with opener.open("http://127.0.0.1:8501/_stcore/health", timeout=0.5) as response:
                    ready = response.status == 200 and response.read().strip() == b"ok"
                if ready and server is not None and helper is not None:
                    break
            except OSError:
                pass
            time.sleep(0.1)
        else:
            raise TimeoutError("Launcher smoke readiness exceeded 35 s")
        result.update(
            health="200 ok",
            launcher_pid=process.pid,
            server_pid=server.pid,
            server_created=server.create_time(),
            helper_pid=helper.pid,
            helper_created=helper.create_time(),
        )
        result["owned_server_listens_8501"] = any(
            connection.status == psutil.CONN_LISTEN
            and connection.laddr.ip == "127.0.0.1"
            and connection.laddr.port == 8501
            for connection in server.net_connections(kind="tcp")
        )
        assert result["owned_server_listens_8501"]
        with opener.open("http://127.0.0.1:8501/", timeout=2) as response:
            result["root_http_status"] = response.status
            result["streamlit_html"] = b"Streamlit" in response.read()
        occupied = subprocess.run(
            [str(launcher)],
            cwd="/private/tmp",
            input="\n",
            text=True,
            capture_output=True,
            timeout=8,
        )
        (evidence / "launcher-occupied.log").write_text(occupied.stdout + occupied.stderr)
        result.update(
            occupied_exit=occupied.returncode,
            occupied_message=occupied.stdout,
            original_server_survived=server.is_running(),
        )
        assert occupied.returncode == 1 and "Port 8501 is unavailable" in occupied.stdout
        assert server.is_running()
        (evidence / "launcher-ready.json").write_text(json.dumps(result, indent=2) + "\n")
        deadline = time.monotonic() + 50
        while time.monotonic() < deadline and not (evidence / "launcher-stop.request").exists():
            time.sleep(0.1)
        assert helper.create_time() == result["helper_created"]
        assert helper.cmdline()[1:] == ["-I", "-S", "-", str(root)]
        helper.send_signal(signal.SIGINT)
        result["launcher_exit_after_helper_sigint"] = process.wait(timeout=8)
        result["server_gone_after_launcher_cleanup"] = (
            not server.is_running() or server.status() == psutil.STATUS_ZOMBIE
        )
        assert result["server_gone_after_launcher_cleanup"]
        with socket.socket() as available:
            available.bind(("127.0.0.1", 8501))
        result["port_bindable_after_shutdown"] = True
    finally:
        if process.poll() is None:
            if server is not None and server.is_running():
                server.terminate()
                server.wait(timeout=5)
            if launch_process.is_running() and launch_process.create_time() == launch_birth:
                process.terminate()
                process.wait(timeout=5)

missing = evidence / "launcher-missing-env"
missing.mkdir()
copy = missing / launcher.name
shutil.copy2(launcher, copy)
assert copy.read_bytes() == launcher.read_bytes()
absent = subprocess.run(
    [str(copy)], cwd="/private/tmp", input="\n", text=True, capture_output=True, timeout=8
)
(evidence / "launcher-missing-env.log").write_text(absent.stdout + absent.stderr)
result.update(missing_environment_exit=absent.returncode, missing_environment_message=absent.stdout)
assert absent.returncode == 1 and "Workbench setup is missing" in absent.stdout
(evidence / "launcher-smoke.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
