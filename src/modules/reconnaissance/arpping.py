from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch


class arpping(APT_MODULE):
    name = "ARP Ping"
    description = (
        "Sends ARP broadcast packets to discover live hosts on the local "
        "network segment. Effective for LAN-level host discovery."
    )
    tactic = AttackTactic.RECONNAISSANCE
    technique_id = "T1595.001"
    technique_name = "Active Scanning: Scanning IP Blocks"
    compatible_os = [TargetOS.ANY]
    compatible_arch = [TargetArch.ANY]

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        from scapy.all import srp  # type: ignore
        from scapy.layers.l2 import Ether, ARP  # type: ignore
        target.log_activity("Sending ARP...", True)
        response, _ = srp(
            Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=target.ip_label), timeout=1, verbose=1)
        target.log_activity("Waiting for response...", True)
        if len(response) < 1:
            target.log_activity("No Response", True, MESSAGE_TYPE.ERROR)
        else:
            target.log_activity("Ping Successful", True, MESSAGE_TYPE.SUCCESS)
            target.update_field("is_alive", True)

    def enable(self, e):
        self.enabled = e
