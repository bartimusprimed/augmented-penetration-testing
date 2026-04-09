import logging
from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch


def _guess_os_from_ttl(ttl: int) -> str:
    """Estimate the operating system from the initial TTL of an ICMP response.

    Common initial TTL values:
      255 → Cisco IOS / network appliance
      128 → Windows
       64 → Linux / macOS / BSD
       60 → older macOS / HP-UX
    The actual TTL observed in the response is reduced by each hop, so we
    round up to the nearest common initial value.
    """
    if ttl > 128:
        return "Network Appliance / Cisco IOS (TTL ~255)"
    if ttl > 64:
        return "Windows (TTL ~128)"
    if ttl > 60:
        return "Linux / macOS / BSD (TTL ~64)"
    return "Unknown / heavily-routed host (TTL ≤60)"


class osidentify(APT_MODULE):
    name = "OS Identify (TTL)"
    description = (
        "Sends an ICMP Echo Request and analyzes the response TTL to estimate "
        "the target operating system. Windows typically uses TTL 128, "
        "Linux/macOS use TTL 64, and network appliances use TTL 255."
    )
    tactic = AttackTactic.RECONNAISSANCE
    technique_id = "T1592.001"
    technique_name = "Gather Victim Host Information: Hardware"
    compatible_os = [TargetOS.ANY]
    compatible_arch = [TargetArch.ANY]

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        from scapy.layers.inet import IP, ICMP  # type: ignore
        from scapy.sendrecv import sr1  # type: ignore

        target.log_activity("Sending ICMP Echo Request for OS fingerprinting...", True)
        response = sr1(
            IP(dst=target.ip_label) / ICMP(), timeout=2, verbose=0)

        if response is None:
            target.log_activity(
                "No ICMP response – host may be down or blocking ICMP pings",
                True, MESSAGE_TYPE.ERROR,
            )
            return

        ttl = response[IP].ttl
        logging.log(logging.DEBUG, f"OS identify: TTL={ttl} from {target.ip_label}")
        os_guess = _guess_os_from_ttl(ttl)
        target.log_activity(f"Response TTL: {ttl} → {os_guess}", True, MESSAGE_TYPE.SUCCESS)
        target.update_field("os_guess", os_guess)
        target.update_field("is_alive", True)

    def enable(self, e):
        self.enabled = e
