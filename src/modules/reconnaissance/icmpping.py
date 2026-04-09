import logging
from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch


class icmpping(APT_MODULE):
    name = "ICMP Ping"
    description = (
        "Sends ICMP Echo Request packets to check if a host is alive and "
        "reachable. Useful for quick host discovery over routed networks."
    )
    tactic = AttackTactic.RECONNAISSANCE
    technique_id = "T1595.001"
    technique_name = "Active Scanning: Scanning IP Blocks"
    compatible_os = [TargetOS.ANY]
    compatible_arch = [TargetArch.ANY]

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        from scapy.layers.inet import IP, ICMP  # type: ignore
        from scapy.sendrecv import sr1  # type: ignore
        target.log_activity("Sending ICMP Echo Request...", True)
        response = sr1(
            IP(dst=target.ip_label) / ICMP(), timeout=2, verbose=0)
        if response is None:
            target.log_activity(
                "No Response (host may be down or blocking ICMP)", True, MESSAGE_TYPE.ERROR)
        else:
            logging.log(logging.DEBUG, f"ICMP Echo Reply received from {response.src}")
            target.log_activity(
                f"ICMP Echo Reply received from {response.src}", True, MESSAGE_TYPE.SUCCESS)
            target.update_field("is_alive", True)

    def enable(self, e):
        self.enabled = e
