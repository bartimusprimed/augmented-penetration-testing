import logging
from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch

COMMON_UDP_PORTS = [
    53, 67, 68, 69, 123, 137, 138, 161, 162,
    500, 514, 520, 1194, 1900, 4500, 5353,
]


class udpscan(APT_MODULE):
    name = "UDP Scan"
    description = (
        "Scans common UDP ports to identify open services such as DNS, SNMP, "
        "DHCP, and NTP. Uses ICMP port-unreachable responses to identify "
        "closed ports."
    )
    tactic = AttackTactic.RECONNAISSANCE
    technique_id = "T1046"
    technique_name = "Network Service Discovery"
    compatible_os = [TargetOS.ANY]
    compatible_arch = [TargetArch.ANY]

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        from scapy.layers.inet import IP, UDP, ICMP  # type: ignore
        from scapy.sendrecv import sr  # type: ignore
        target.log_activity(
            f"Starting UDP scan on {len(COMMON_UDP_PORTS)} common ports...", True)
        answered, _ = sr(
            IP(dst=target.ip_label) / UDP(dport=COMMON_UDP_PORTS),
            timeout=2, verbose=0,
        )
        open_ports = []
        for sent, received in answered:
            if received.haslayer(UDP):
                port = sent[UDP].dport
                open_ports.append(port)
                target.log_activity(f"Port {port}/udp open")
                logging.log(logging.DEBUG, f"UDP response received on port {port} from {target.ip_label}")
            elif received.haslayer(ICMP) and int(received[ICMP].type) == 3:
                # ICMP port-unreachable means definitively closed; skip silently
                pass
        if open_ports:
            target.log_activity(
                f"Found {len(open_ports)} open UDP port(s): {', '.join(map(str, sorted(open_ports)))}",
                True, MESSAGE_TYPE.SUCCESS,
            )
            merged = list(target.ports)
            for p in open_ports:
                if p not in merged:
                    merged.append(p)
            target.update_field("ports", merged)
            target.update_field("is_alive", True)
        else:
            target.log_activity(
                "No open UDP ports found on scanned common ports", True, MESSAGE_TYPE.INFORMATION)

    def enable(self, e):
        self.enabled = e
