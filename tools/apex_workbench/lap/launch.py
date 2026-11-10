"""Small V2 launch entrypoint, same owned-listener convention and approved environment."""

import os
import socket
import subprocess
import sys
import time
import urllib.request

import psutil

from tools.apex_workbench.configuration import ROOT

APP = ROOT / "tools/apex_workbench/lap/app.py"
URL = "http://127.0.0.1:8503"


def listener():
    found = subprocess.run(
        ["/usr/sbin/lsof", "-nP", "-iTCP@127.0.0.1:8503", "-sTCP:LISTEN", "-Fp"],
        capture_output=True,
        text=True,
        timeout=2,
    )
    pids = [int(r[1:]) for r in found.stdout.splitlines() if r.startswith("p")]
    if len(pids) == 1:
        process = psutil.Process(pids[0])
        if (
            process.uids().real == os.getuid()
            and process.cwd() == str(ROOT)
            and process.cmdline()[1:5] == ["-m", "streamlit", "run", str(APP)]
        ):
            return process
    return None


def healthy():
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
            URL + "/_stcore/health", timeout=0.5
        ) as response:
            return response.status == 200 and response.read().strip() == b"ok"
    except OSError:
        return False


def main():
    process = None
    try:
        existing = listener()
        if existing and healthy():
            subprocess.run(["/usr/bin/open", URL], check=False)
            print("Reusing this checkout's owned V2 workspace.")
            return 0
        with socket.socket() as port:
            try:
                port.bind(("127.0.0.1", 8503))
            except OSError:
                print("Port8503 is occupied. V2 did not stop or replace its owner.")
                return 1
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(APP),
                "--server.address",
                "127.0.0.1",
                "--server.port",
                "8503",
                "--server.headless",
                "true",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=ROOT,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and process.poll() is None:
            if healthy() and (owned := listener()) is not None and owned.pid == process.pid:
                print(
                    "V2 ready. Keep this Terminal open; Control-C stops its owned server.",
                    flush=True,
                )
                subprocess.run(["/usr/bin/open", URL], check=False)
                return process.wait()
            time.sleep(0.1)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
