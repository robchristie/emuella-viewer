import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("check_stobie_cli", Path(__file__).resolve().parents[1] / "check-stobie-cli.py")
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)

REV = "0123456789abcdef0123456789abcdef01234567"


def manifest(*lines: str) -> Path:
    directory = Path(tempfile.mkdtemp())
    path = directory / "Cargo.toml"
    path.write_text("[workspace.dependencies]\nserde = \"1\"\n" + "\n".join(lines) + "\n")
    return path


class Patched(unittest.TestCase):
    def test_only_a_stobie_patch_counts(self):
        directory = Path(tempfile.mkdtemp())
        config = directory / "config.toml"
        self.assertFalse(check.patched(config))
        config.write_text('[patch."https://github.com/other/repo"]\nx = { path = "/x" }\n')
        self.assertFalse(check.patched(config))
        config.write_text(f'[patch."{check.STOBIE_GIT}"]\nstobie-core = {{ path = "/s/crates/stobie-core" }}\n')
        self.assertTrue(check.patched(config))


class PinnedRevision(unittest.TestCase):
    def test_one_full_revision_is_accepted(self):
        path = manifest(*(f'stobie-{name} = {{ git = "{check.STOBIE_GIT}", rev = "{REV}" }}' for name in ("core", "ui-egui")))
        self.assertEqual(check.pinned_revision(path), REV)

    def test_mixed_short_or_branch_pins_are_rejected(self):
        for lines in (
            (f'stobie-core = {{ git = "{check.STOBIE_GIT}", rev = "{REV}" }}', f'stobie-ui-egui = {{ git = "{check.STOBIE_GIT}", rev = "{"1" * 40}" }}'),
            (f'stobie-core = {{ git = "{check.STOBIE_GIT}", rev = "0123456" }}',),
            (f'stobie-core = {{ git = "{check.STOBIE_GIT}", branch = "main" }}',),
            ('stobie-core = { path = "../stobie/crates/stobie-core" }',),
        ):
            with self.subTest(lines=lines), self.assertRaises(SystemExit):
                check.pinned_revision(manifest(*lines))

    def test_this_repository_pins_one_revision(self):
        self.assertRegex(check.pinned_revision(), r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
