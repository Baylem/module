"""Exercise the catalog command on disposable volumes in the pinned ARK image."""

import json
from pathlib import Path
import subprocess
import unittest

import yaml


class ArkVolumeMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parent / "ark-survival-evolved/template.yaml"
        spec = yaml.safe_load(path.read_text())["spec"]
        images = {}
        references = [spec["image"]]
        for version in spec["versions"]:
            if version.get("image"):
                references.append(version["image"])
        for reference in references:
            # The default and version tag can name the same immutable image.
            digest = reference.partition("@")[2]
            images.setdefault(digest or reference, reference)
        cls.images = list(images.values())
        cls.argv = (spec.get("command") or ["/docker-entrypoint.sh"]) + (spec.get("args") or [])
        for reference in cls.images:
            subprocess.run(["docker", "pull", "--platform", "linux/amd64", reference], check=True)
            image = json.loads(subprocess.check_output(["docker", "image", "inspect", reference]))[0]
            original = image["Config"]
            if original["Entrypoint"] != ["/docker-entrypoint.sh"] or original.get("Cmd"):
                raise AssertionError(f"Review the vendor startup command for {reference}")

    def test_real_vendor_handoff(self):
        # This validation is the first action of the genuine pinned entrypoint.
        # It establishes the handoff before SteamCMD runs or writes a game.
        for image in self.images:
            with self.subTest(image=image):
                result = subprocess.run(
                    ["docker", "run", "--rm", "--pull=never", "--network=none", "--read-only",
                     "--cap-drop=ALL", "--security-opt=no-new-privileges", "--tmpfs", "/app",
                     "--tmpfs", "/cluster", "--env", "UPDATE_WARN_MINUTES=not-a-number",
                     "--entrypoint", self.argv[0], image, *self.argv[1:]],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                self.assertIn("UPDATE_WARN_MINUTES must be a whole number", result.stdout + result.stderr)

    def test_startup(self):
        world = "mkdir -p /app/ShooterGame/Saved/SavedArks; echo survivor >/app/ShooterGame/Saved/SavedArks/TheIsland.ark"
        migrated = "mkdir -p /app/server/ShooterGame/Saved/SavedArks; echo survivor >/app/server/ShooterGame/Saved/SavedArks/TheIsland.ark"
        old_cluster = "/app/server/ShooterGame/Saved/clusters"
        cases = [
            ("fresh volume", "mkdir /app/lost+found", True),
            ("migrated world and uploads", migrated + "; echo dino >/cluster/tribe", True),
            ("empty old cluster folders", migrated + f"; mkdir -p {old_cluster}/empty", True),
            ("legacy world", world, False),
            ("1.0 Saved-only PVC", "mkdir /app/SavedArks; echo survivor >/app/SavedArks/TheIsland.ark", False),
            ("1.0 transfer-only PVC", "mkdir -p /app/clusters/id; echo dino >/app/clusters/id/.upload", False),
            ("1.0 layout moved one level", "mkdir -p /app/server/SavedArks; echo survivor >/app/server/SavedArks/TheIsland.ark", False),
            ("partial 1.0 layout and new saves", migrated + "; mkdir /app/Config", False),
            ("old and new worlds", world + "; " + migrated, False),
            ("partially moved install", migrated + "; mkdir /app/Engine", False),
            ("unmigrated cluster upload", migrated + f"; mkdir -p {old_cluster}/id; echo dino >{old_cluster}/id/.upload", False),
            ("conflicting cluster uploads", migrated + f"; mkdir -p {old_cluster}; echo old >{old_cluster}/tribe; echo new >/cluster/tribe", False),
            ("broken legacy symlink", "ln -s /missing /app/ShooterGame", False),
            ("symlink in target path", "ln -s /missing /app/server", False),
            ("inaccessible target", "mkdir /app/server; chmod 000 /app/server", False),
            ("unreadable old transfer folder", f"mkdir -p {old_cluster}/id; chmod 000 {old_cluster}/id", False),
            ("non-directory save path", "mkdir -p /app/server/ShooterGame; touch /app/server/ShooterGame/Saved", False),
            ("redirected vendor storage", "export ARK_SERVER_VOLUME=/tmp", False),
            ("missing cluster mount", "mkdir -p /cluster", False),
        ]
        # Replace only the vendor entrypoint in this throwaway container. A
        # successful guard must exec it as PID 1 without downloading the game.
        setup = """
            test -x /docker-entrypoint.sh
            printf '%s\n' '#!/bin/sh' '[ ! -s /tmp/save-hashes ] || sha256sum -c --status /tmp/save-hashes || exit 93' 'echo "VENDOR PID=$$"' > /docker-entrypoint.sh
            : > /dev/termination-log
        """
        snapshot = """
            for file in /app/SavedArks/TheIsland.ark /app/clusters/id/.upload /app/server/SavedArks/TheIsland.ark \
                    /app/ShooterGame/Saved/SavedArks/TheIsland.ark \
                    /app/server/ShooterGame/Saved/SavedArks/TheIsland.ark \
                    /app/server/ShooterGame/Saved/clusters/id/.upload \
                    /app/server/ShooterGame/Saved/clusters/tribe /cluster/tribe; do
                if [ -f "$file" ]; then sha256sum "$file"; fi
            done > /tmp/save-hashes
        """
        for image in self.images:
            for name, fixture, allowed in cases:
                args = ["docker", "run", "--rm", "--pull=never", "--network=none",
                        "--cap-drop=ALL", "--security-opt=no-new-privileges", "--tmpfs", "/app"]
                if name != "missing cluster mount":
                    args += ["--tmpfs", "/cluster"]
                check = """
                    set +e
                    "$@"
                    status=$?
                    set -e
                    [ ! -s /tmp/save-hashes ] || sha256sum -c --status /tmp/save-hashes
                    test "$status" = 78 && grep -q 'ARK storage check' /dev/termination-log
                """
                script = setup + "\n" + fixture + "\n" + snapshot + ('exec "$@"' if allowed else check)
                with self.subTest(name=name, image=image):
                    result = subprocess.run(args + ["--entrypoint", "/bin/sh", image, "-ec",
                                            script, "test", *self.argv], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    if allowed:
                        self.assertIn("VENDOR PID=1", result.stdout)
                    else:
                        self.assertNotIn("VENDOR", result.stdout)
                        self.assertIn("ARK storage check", result.stderr)


if __name__ == "__main__":
    unittest.main()
