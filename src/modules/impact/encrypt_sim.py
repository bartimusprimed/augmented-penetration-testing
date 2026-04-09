import logging

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from utils.ssh_helper import ssh_exec

_TEST_CONTENT = "APT impact simulation – this file has been 'encrypted' (base64 encoded)."
_REMOTE_PLAIN = "/tmp/apt_impact.txt"
_REMOTE_ENC = "/tmp/apt_impact.txt.b64"


class encrypt_sim(APT_MODULE):
    name = "Encrypt Simulation"
    description = (
        "Simulates a ransomware-style encryption impact by writing a plaintext test file "
        "on the target and base64-encoding it in place. Demonstrates the ability to "
        "modify files without deploying actual malware."
    )
    tactic = AttackTactic.IMPACT
    technique_id = "T1486"
    technique_name = "Data Encrypted for Impact"
    compatible_os = [TargetOS.LINUX, TargetOS.MACOS]
    compatible_arch = [TargetArch.ANY]

    ssh_user = "root"
    ssh_port = 22
    ssh_key_path = "~/.ssh/id_rsa"

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        # Step 1: write the test plaintext file
        target.log_activity(f"Writing test file {_REMOTE_PLAIN} on target...", True)
        write_cmd = f"echo '{_TEST_CONTENT}' > {_REMOTE_PLAIN}"
        stdout, stderr, rc = ssh_exec(
            target.ip_label, write_cmd,
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        if rc != 0:
            logging.log(logging.ERROR, f"encrypt_sim write [{target.ip_label}]: {stderr}")
            target.log_activity(
                f"Failed to write test file: {stderr.strip()}", True, MESSAGE_TYPE.ERROR)
            return
        target.log_activity(f"Test file written: {_REMOTE_PLAIN}")

        # Step 2: base64-encode the file (simulating encryption)
        target.log_activity("Base64-encoding (simulating encryption)...", True)
        encode_cmd = f"base64 {_REMOTE_PLAIN} > {_REMOTE_ENC} && cat {_REMOTE_ENC}"
        stdout, stderr, rc = ssh_exec(
            target.ip_label, encode_cmd,
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        if rc != 0:
            logging.log(logging.ERROR, f"encrypt_sim encode [{target.ip_label}]: {stderr}")
            target.log_activity(
                f"Encoding failed: {stderr.strip()}", True, MESSAGE_TYPE.ERROR)
            return

        encoded = stdout.strip()
        target.log_activity(f"Encoded file ({_REMOTE_ENC}):\n{encoded}")
        target.log_activity(
            f"Simulation complete – {_REMOTE_PLAIN} encoded to {_REMOTE_ENC}",
            True, MESSAGE_TYPE.SUCCESS,
        )

    def enable(self, e):
        self.enabled = e
