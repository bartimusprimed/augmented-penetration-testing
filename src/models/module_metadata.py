import enum


class AttackTactic(enum.Enum):
    RECONNAISSANCE = ("TA0043", "Reconnaissance")
    RESOURCE_DEVELOPMENT = ("TA0042", "Resource Development")
    INITIAL_ACCESS = ("TA0001", "Initial Access")
    EXECUTION = ("TA0002", "Execution")
    PERSISTENCE = ("TA0003", "Persistence")
    PRIVILEGE_ESCALATION = ("TA0004", "Privilege Escalation")
    DEFENSE_EVASION = ("TA0005", "Defense Evasion")
    CREDENTIAL_ACCESS = ("TA0006", "Credential Access")
    DISCOVERY = ("TA0007", "Discovery")
    LATERAL_MOVEMENT = ("TA0008", "Lateral Movement")
    COLLECTION = ("TA0009", "Collection")
    COMMAND_AND_CONTROL = ("TA0011", "Command and Control")
    EXFILTRATION = ("TA0010", "Exfiltration")
    IMPACT = ("TA0040", "Impact")

    def __init__(self, tactic_id: str, display_name: str):
        self.tactic_id = tactic_id
        self.display_name = display_name


class TargetOS(enum.Enum):
    WINDOWS = "Windows"
    LINUX = "Linux"
    MACOS = "macOS"
    ANY = "Any"


class TargetArch(enum.Enum):
    X86 = "x86"
    X86_64 = "x86_64"
    ARM = "ARM"
    ARM64 = "ARM64"
    ANY = "Any"
