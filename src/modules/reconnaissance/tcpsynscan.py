import logging
from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
    143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080,
]


class tcpsynscan(APT_MODULE):
    name = "TCP SYN Scan"
    description = (
        "Performs a stealthy TCP SYN scan on common ports to enumerate open "
        "services. Sends SYN packets and inspects SYN-ACK responses without "
        "completing the handshake."
    )
    tactic = AttackTactic.RECONNAISSANCE
    technique_id = "T1046"
    technique_name = "Network Service Discovery"
    compatible_os = [TargetOS.ANY]
    compatible_arch = [TargetArch.ANY]

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        from scapy.layers.inet import IP, TCP  # type: ignore
        from scapy.sendrecv import sr  # type: ignore
        target.log_activity(
            f"Starting TCP SYN scan on {len(COMMON_PORTS)} common ports...", True)
        answered, _ = sr(
            IP(dst=target.ip_label) / TCP(dport=COMMON_PORTS, flags="S"),
            timeout=2, verbose=0,
        )
        open_ports = []
        for sent, received in answered:
            if received.haslayer(TCP) and received[TCP].flags & 0x12 == 0x12:
                port = sent[TCP].dport
                open_ports.append(port)
                target.log_activity(f"Port {port}/tcp open")
                logging.log(logging.DEBUG, f"TCP SYN-ACK received on port {port} from {target.ip_label}")
                _, _ = sr(
                    IP(dst=target.ip_label) / TCP(dport=port, flags="R"),
                    timeout=1, verbose=0,
                )
        if open_ports:
            target.log_activity(
                f"Found {len(open_ports)} open port(s): {', '.join(map(str, sorted(open_ports)))}",
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
                "No open ports found on scanned common ports", True, MESSAGE_TYPE.INFORMATION)

    def enable(self, e):
        self.enabled = e
