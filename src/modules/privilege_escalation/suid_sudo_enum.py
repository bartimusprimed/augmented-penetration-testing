import logging

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from utils.ssh_helper import ssh_exec


class suid_sudo_enum(APT_MODULE):
    name = "SUID/SUDO Enumeration"
    description = (
        "Uses the native `find` binary to enumerate SUID/SGID executables on the target, "
        "then runs `sudo -l` to identify commands the current user may execute with elevated "
        "privileges. Results highlight common privilege-escalation vectors."
    )
    tactic = AttackTactic.PRIVILEGE_ESCALATION
    technique_id = "T1548.001"
    technique_name = "Abuse Elevation Control Mechanism: Setuid and Setgid"
    compatible_os = [TargetOS.LINUX, TargetOS.MACOS]
    compatible_arch = [TargetArch.ANY]

    ssh_user = "root"
    ssh_port = 22
    ssh_key_path = "~/.ssh/id_rsa"

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        # --- SUID binaries ---
        target.log_activity("Enumerating SUID/SGID binaries via find...", True)
        stdout, stderr, rc = ssh_exec(
            target.ip_label,
            "find / -perm /6000 -type f 2>/dev/null",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        if rc == 0:
            lines = [l for l in stdout.strip().splitlines() if l]
            if lines:
                target.log_activity(f"Found {len(lines)} SUID/SGID binaries:")
                for line in lines:
                    target.log_activity(f"  {line}")
                target.log_activity(
                    f"{len(lines)} SUID/SGID binaries found", True, MESSAGE_TYPE.SUCCESS)
            else:
                target.log_activity("No SUID/SGID binaries found", True, MESSAGE_TYPE.INFORMATION)
        else:
            logging.log(logging.ERROR, f"suid_sudo_enum find [{target.ip_label}]: {stderr}")
            target.log_activity(f"find error: {stderr.strip()}", True, MESSAGE_TYPE.ERROR)

        # --- sudo -l ---
        target.log_activity("Checking sudo privileges...", True)
        stdout, stderr, rc = ssh_exec(
            target.ip_label,
            "sudo -l 2>&1",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        output = stdout.strip() or stderr.strip()
        if output:
            target.log_activity(f"sudo -l output:\n{output}", True, MESSAGE_TYPE.SUCCESS)
        else:
            target.log_activity("No sudo output returned", True, MESSAGE_TYPE.INFORMATION)

    def enable(self, e):
        self.enabled = e
