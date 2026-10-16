import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "check_tracked_files", Path(__file__).resolve().parents[1] / "check-tracked-files.py"
)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class TrackedFilePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.check_call(["git", "-C", str(self.root), "init", "-q"])

    def add(self, path, data=b"text\n"):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        subprocess.check_call(["git", "-C", str(self.root), "add", "--", path])

    def violations(self):
        return policy.violations(self.root, policy.tracked(self.root))

    def test_summaries_and_receipts_pass(self):
        self.add("docs/example-evidence/README.md")
        self.add("docs/example-evidence.md")
        self.add("docs/results.json", b"{}\n")
        self.add("apps/emuella-viewer/qualification/thresholds.json", b"{}\n")
        self.assertEqual(self.violations(), [])

    def test_imagery_and_prepared_scenes_are_rejected(self):
        for path in ("scene.ntf", "data/scene.NITF", "prepared/codestream.j2k",
                     "prepared/image.jp2", "prepared/tile.jph", "raster.tif"):
            with self.subTest(path=path):
                self.add(path, b"text-looking bytes\n")
                self.assertTrue(any(v.startswith(path + ": binary") for v in self.violations()))

    def test_raw_evidence_is_rejected_whatever_its_format(self):
        for path in ("docs/example-evidence/capture.png",
                     "docs/example-evidence/run/observations.json",
                     "docs/example-evidence/runtime.log",
                     "docs/example-evidence.json"):
            with self.subTest(path=path):
                self.add(path)
                self.assertTrue(any(v.startswith(path + ": raw evidence") for v in self.violations()))

    def test_binary_outside_reviewed_roots_is_rejected_by_suffix_or_content(self):
        self.add("docs/overview.png", b"not really a png\n")
        self.add("tools/data/blob", b"header\0payload")
        found = self.violations()
        self.assertTrue(any(v.startswith("docs/overview.png: binary") for v in found))
        self.assertTrue(any(v.startswith("tools/data/blob: binary") for v in found))

    def test_size_limits_apply_by_kind(self):
        self.add("docs/large.json", b"x" * (policy.TEXT_LIMIT_BYTES + 1))
        self.add("docs/limit.json", b"x" * policy.TEXT_LIMIT_BYTES)
        self.add("docs/large.webp", b"\0" * (policy.BINARY_LIMIT_BYTES + 1))
        found = [v for v in self.violations() if "exceeds" in v]
        self.assertEqual(sorted(v.split(":")[0] for v in found),
                         ["docs/large.json", "docs/large.webp"])
        self.assertIn("binary limit", next(v for v in found if v.startswith("docs/large.webp")))
        self.assertIn("text limit", next(v for v in found if v.startswith("docs/large.json")))

    def test_only_tracked_present_files_are_checked(self):
        untracked = self.root / "docs/example-evidence/untracked.png"
        untracked.parent.mkdir(parents=True)
        untracked.write_bytes(b"\0")
        self.add("docs/example-evidence/deleted.png")
        (self.root / "docs/example-evidence/deleted.png").unlink()
        self.assertEqual(self.violations(), [])


if __name__ == "__main__":
    unittest.main()
