import logging
import os
import subprocess


def ssh_exec(
    ip: str,
    command: str,
    user: str = "root",
    port: int = 22,
    key_path: str = "~/.ssh/id_rsa",
    timeout: int = 30,
) -> tuple[str, str, int]:
    """Execute a command on a remote host via SSH using key-based authentication."""
    key = os.path.expanduser(key_path)
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-i", key,
        "-p", str(port),
        f"{user}@{ip}",
        command,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        logging.log(logging.DEBUG, f"SSH [{ip}] rc={result.returncode} cmd={command!r}")
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "SSH connection timed out", 1
    except Exception as ex:
        logging.log(logging.ERROR, f"SSH exec error [{ip}]: {ex}")
        return "", str(ex), 1


def scp_get(
    ip: str,
    remote_path: str,
    local_path: str,
    user: str = "root",
    port: int = 22,
    key_path: str = "~/.ssh/id_rsa",
    timeout: int = 60,
) -> tuple[bool, str]:
    """Copy a file from a remote host to a local path using SCP."""
    key = os.path.expanduser(key_path)
    cmd = [
        "scp",
        "-o", "StrictHostKeyChecking=no",
        "-i", key,
        "-P", str(port),
        f"{user}@{ip}:{remote_path}",
        local_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, local_path
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "SCP timed out"
    except Exception as ex:
        logging.log(logging.ERROR, f"SCP error [{ip}]: {ex}")
        return False, str(ex)
