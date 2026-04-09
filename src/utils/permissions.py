import glob
import grp
import logging
import os
import sys


def _access_bpf_group_exists() -> bool:
    """Return True if the ``access_bpf`` group exists on the system."""
    try:
        grp.getgrnam("access_bpf")
        return True
    except KeyError:
        return False


def check_raw_packet_access() -> str | None:
    """Check whether raw packet operations will succeed on the current platform.

    Returns None when no problems are detected, or a human-readable warning
    string that should be displayed to the user before modules are run.

    On macOS the function distinguishes two cases:
    1. Running as root (UID 0) – macOS's WindowServer refuses GUI connections
       from root processes, so this can never work correctly.
    2. Not in the ``access_bpf`` group – Scapy uses BPF devices on macOS and
       cannot open them without the appropriate group membership or root.
    """
    if sys.platform != "darwin":
        return None

    if os.getuid() == 0:
        return (
            "APT is running as root (sudo), which is NOT supported on macOS.\n\n"
            "macOS blocks GUI applications from rendering when they run as root "
            "because the WindowServer refuses connections from UID 0. This causes "
            "the app to hang on the 'Working…' screen indefinitely.\n\n"
            "Instead, run APT as your normal user and grant BPF device access "
            "so that Scapy modules can send raw packets without sudo:\n\n"
            "  sudo dseditgroup -o edit -a \"$USER\" -t user access_bpf\n\n"
            "Log out and back in for the group change to take effect, "
            "then start APT normally (without sudo)."
        )

    # Check whether /dev/bpf* devices are readable by the current user.
    # Scapy on macOS uses BPF for all raw packet send/receive operations.
    bpf_devices = glob.glob("/dev/bpf*")
    if not bpf_devices:
        # No BPF devices present – unusual but not immediately an error.
        return None

    # Try each BPF device; return None (no warning) as soon as one is readable.
    # If every attempt raises PermissionError the loop exhausts and we fall
    # through to return the warning message below.
    for bpf_dev in bpf_devices:
        try:
            with open(bpf_dev, "rb"):
                return None  # at least one BPF device is accessible
        except PermissionError:
            pass
        except OSError:
            pass

    logging.log(
        logging.WARNING,
        "macOS: /dev/bpf* devices are not readable – Scapy modules will fail "
        "with PermissionError when executed",
    )

    if not _access_bpf_group_exists():
        return (
            "Raw packet modules (ARP ping, ICMP ping, TCP SYN scan, UDP scan) "
            "need BPF device access on macOS, but the \"access_bpf\" group does "
            "not exist on this system.\n\n"
            "The access_bpf group is created automatically when Wireshark is "
            "installed. Install Wireshark from https://www.wireshark.org, then "
            "add yourself to the group:\n\n"
            "  sudo dseditgroup -o edit -a \"$USER\" -t user access_bpf\n\n"
            "Log out and back in, then restart APT.\n\n"
            "Do NOT run APT with sudo – macOS blocks GUI apps running as root."
        )

    return (
        "Raw packet modules (ARP ping, ICMP ping, TCP SYN scan, UDP scan) "
        "need BPF device access on macOS.\n\n"
        "Grant access once with:\n\n"
        "  sudo dseditgroup -o edit -a \"$USER\" -t user access_bpf\n\n"
        "Log out and back in, then restart APT.\n\n"
        "Do NOT run APT with sudo – macOS blocks GUI apps running as root."
    )
