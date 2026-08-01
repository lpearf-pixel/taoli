import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectTests(unittest.TestCase):
    def test_template_preserves_old_proxy_settings_chain(self):
        data = json.loads((ROOT / "config/config.template.json").read_text(encoding="utf-8"))
        outbounds = {item["tag"]: item for item in data["outbounds"]}
        vmess = outbounds["out"]
        self.assertEqual(vmess["protocol"], "vmess")
        self.assertEqual(vmess["proxySettings"], {"tag": "transit", "transportLayer": False})
        self.assertNotIn("streamSettings", vmess)
        vless = outbounds["transit"]
        self.assertEqual(vless["protocol"], "vless")
        self.assertEqual(vless["streamSettings"]["security"], "reality")
        self.assertEqual(vless["streamSettings"]["method"], "raw")
        self.assertFalse(vmess["mux"]["enabled"])
        self.assertFalse(vless["mux"]["enabled"])

    def test_renderer_creates_typed_xray_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(ROOT, project, ignore=shutil.ignore_patterns(".env", "config.json", "__pycache__"))
            env = (project / ".env.example").read_text(encoding="utf-8")
            env = env.replace("REPLACE_WITH_VLESS_UUID", "11111111-1111-4111-8111-111111111111")
            env = env.replace("REPLACE_WITH_REALITY_PUBLIC_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            env = env.replace("REPLACE_WITH_REALITY_SHORT_ID", "0123456789abcdef")
            env = env.replace("REPLACE_WITH_US_VMESS_UUID", "22222222-2222-4222-8222-222222222222")
            (project / ".env").write_text(env, encoding="utf-8")
            result = subprocess.run(
                ["python3", "scripts/render_config.py"],
                cwd=project,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads((project / "config/config.json").read_text(encoding="utf-8"))
            outbounds = {item["tag"]: item for item in data["outbounds"]}
            self.assertEqual(outbounds["out"]["settings"]["port"], 18868)
            self.assertIsInstance(outbounds["out"]["settings"]["port"], int)
            self.assertEqual(outbounds["transit"]["settings"]["port"], 443)
            self.assertEqual(outbounds["out"]["proxySettings"]["tag"], "transit")
            self.assertEqual((project / "config/config.json").stat().st_mode & 0o777, 0o600)

    def test_secrets_are_not_committed(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".env", ignored)
        self.assertIn("config/config.json", ignored)
        self.assertFalse((ROOT / ".env").exists())
        self.assertFalse((ROOT / "config/config.json").exists())


if __name__ == "__main__":
    unittest.main()
