"""Verify the Minecraft Java startup settings with their pinned image launcher."""

from pathlib import Path
import shlex
import subprocess
import unittest

import yaml


class MinecraftStartup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parent / "minecraft-java/template.yaml"
        template = yaml.safe_load(path.read_text())["spec"]
        cls.image = template["image"]
        cls.fields = {f["name"]: f for f in template["configSchema"]}

    def launch(self, **env):
        args = ["docker", "run", "--rm", "--platform", "linux/amd64", "--network", "none",
                "--tmpfs", "/data", "--entrypoint", "/image/scripts/start-finalExec"]
        for name, value in {**env, "SETUP_ONLY": "true", "VERSION": "1.21.4",
                            "TYPE": "VANILLA", "SERVER": "server.jar"}.items():
            args.extend(("-e", f"{name}={value}"))
        output = subprocess.check_output([*args, self.image], text=True, encoding="utf-8")
        command = next(line for line in output.splitlines() if line.startswith("SETUP_ONLY: java "))
        return shlex.split(command)

    def test_automatic_and_explicit_settings(self):
        for name in ["INIT_MEMORY", "MAX_MEMORY", "JVM_OPTS", "JVM_XX_OPTS", "USE_AIKAR_FLAGS"]:
            self.assertTrue(self.fields[name]["applyOnRestart"])
        self.assertEqual(self.fields["USE_AIKAR_FLAGS"]["default"], "false")
        # The operator sends whole MiB for each autoFromMemoryLimit field.
        env = {}
        for name in ["INIT_MEMORY", "MAX_MEMORY"]:
            percent = self.fields[name]["autoFromMemoryLimit"]["percent"]
            self.assertEqual(percent, 75)
            env[name] = f"{4096 * percent // 100}M"
        args = self.launch(**env)
        self.assertIn("-Xms3072M", args)
        self.assertIn("-Xmx3072M", args)
        self.assertNotIn("-Daikars.new.flags=true", args)
        args = self.launch(INIT_MEMORY="37.5%", MAX_MEMORY="2G", JVM_OPTS="-Dexample=true",
                           JVM_XX_OPTS="-XX:+PrintCommandLineFlags", USE_AIKAR_FLAGS="true")
        for flag in ["-XX:InitialRAMPercentage=37.5", "-Xmx2G", "-Dexample=true",
                     "-XX:+PrintCommandLineFlags", "-Daikars.new.flags=true"]:
            self.assertIn(flag, args)
        args = self.launch(INIT_MEMORY="512M", MAX_MEMORY="75%")
        self.assertIn("-Xms512M", args)
        self.assertIn("-XX:MaxRAMPercentage=75", args)


if __name__ == "__main__":
    unittest.main()
