import logging

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from utils.ssh_helper import ssh_exec


class user_process_enum(APT_MODULE):
    name = "User & Process Enumeration"
    description = (
        "Enumerates local user accounts by parsing /etc/passwd and lists all running "
        "processes via `ps aux`. Useful for understanding the target's user landscape "
        "and spotting interesting processes."
    )
    tactic = AttackTactic.DISCOVERY
    technique_id = "T1087.001"
    technique_name = "Account Discovery: Local Account"
    compatible_os = [TargetOS.LINUX, TargetOS.MACOS]
    compatible_arch = [TargetArch.ANY]

    ssh_user = "root"
    ssh_port = 22
    ssh_key_path = "~/.ssh/id_rsa"

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        # --- User enumeration via /etc/passwd ---
        target.log_activity("Enumerating local users from /etc/passwd...", True)
        stdout, stderr, rc = ssh_exec(
            target.ip_label, "cat /etc/passwd",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )

        if rc == 0 and stdout.strip():
            users = [l.split(":")[0] for l in stdout.strip().splitlines() if l]
            target.log_activity(f"Found {len(users)} accounts:")
            for u in users:
                target.log_activity(f"  {u}")
            target.log_activity(
                f"{len(users)} local accounts found", True, MESSAGE_TYPE.SUCCESS)
        else:
            logging.log(logging.ERROR, f"user_process_enum passwd [{target.ip_label}]: {stderr}")
            target.log_activity(
                f"Could not read /etc/passwd: {stderr.strip()}", True, MESSAGE_TYPE.ERROR)

        # --- Running process enumeration ---
        target.log_activity("Listing running processes via ps aux...", True)
        stdout, stderr, rc = ssh_exec(
            target.ip_label, "ps aux 2>&1",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )

        if rc == 0 and stdout.strip():
            lines = stdout.strip().splitlines()
            target.log_activity(f"Running processes ({len(lines) - 1} entries):")
            for line in lines:
                target.log_activity(f"  {line}")
            target.log_activity(
                f"{len(lines) - 1} processes listed", True, MESSAGE_TYPE.SUCCESS)
        else:
            logging.log(logging.ERROR, f"user_process_enum ps [{target.ip_label}]: {stderr}")
            target.log_activity(
                f"ps aux failed: {stderr.strip()}", True, MESSAGE_TYPE.ERROR)

    def enable(self, e):
        self.enabled = e
