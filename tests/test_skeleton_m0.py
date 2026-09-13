import tempfile
import unittest
from pathlib import Path
from PIL import Image
from analysis_skeleton.common import write_jsonl, read_jsonl, check_frozen
from analysis_skeleton.m0_data import build


class DataTests(unittest.TestCase):
    def test_missing_partner_and_bad_image_are_retained(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_jsonl(root / "a.jsonl", [{"image_id": 1, "caption": "A car."}, {"image_id": 2, "caption": ""}])
            write_jsonl(root / "b.jsonl", [{"image_id": 1, "caption": "Car."}])
            Image.new("RGB", (3, 3)).save(root / "COCO_val2014_000000000001.jpg")
            (root / "COCO_val2014_000000000002.jpg").write_text("broken")
            result = build(root / "a.jsonl", root / "b.jsonl", root, root / "out")
            self.assertEqual(result["roster_rows"], 2)
            self.assertEqual(result["unpaired"], 1)
            self.assertEqual(result["image_readable"], 1)
            self.assertEqual(read_jsonl(root / "out/pairs.jsonl")[1]["image_status"], "unreadable")
            check_frozen(root / "out")
            (root / "a.jsonl").write_text("changed")
            with self.assertRaises(ValueError):
                check_frozen(root / "out")

    def test_duplicate_fails_without_creating_run(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rows = [{"image_id": 1, "caption": "x"}] * 2
            write_jsonl(root / "a.jsonl", rows)
            with self.assertRaises(ValueError):
                build(root / "a.jsonl", root / "a.jsonl", root, root / "out")
            self.assertFalse((root / "out").exists())
