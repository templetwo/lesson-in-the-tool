"""A lesson must pass true success and catch false success, beyond the count."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lesson_tools import save_records


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "records.jsonl"
        self.records = [{"id": "alpha", "value": 1}, {"id": "beta", "value": 2}]

    def write_bytes(self, payload):
        def writer(path, wanted):
            path.write_bytes(payload)
            return {"status": "ok", "records": 2}
        return writer

    def write_values(self, values):
        return self.write_bytes(("\n".join(json.dumps(row) for row in values) + "\n").encode())

    def test_real_save_confirms_contents_and_copies_hashes(self):
        receipt = save_records(self.path, self.records)
        self.assertEqual(receipt["observation"]["status"], "confirmed")
        self.assertEqual(receipt["observation"]["record_count"], 2)
        self.assertEqual(receipt["intent"]["content_sha256"], receipt["observation"]["content_sha256"])
        self.assertEqual(receipt["intent"]["destination"], str(self.path))
        self.assertEqual(receipt["action"]["claim"]["records"], 2)
        self.assertIsNone(receipt["action"]["error"])
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_false_acknowledgment_cannot_confirm_missing_file(self):
        receipt = save_records(self.path, self.records, writer=lambda path, data: {"status": "ok"})
        self.assertEqual(receipt["action"]["claim"]["status"], "ok")
        self.assertEqual(receipt["observation"]["status"], "contradicted")
        self.assertIsNone(receipt["observation"]["record_count"])

    def test_partial_save_is_contradicted(self):
        receipt = save_records(self.path, self.records, writer=self.write_values(self.records[:1]))
        self.assertEqual(receipt["observation"]["status"], "contradicted")
        self.assertEqual(receipt["observation"]["record_count"], 1)

    def test_equal_count_does_not_hide_wrong_identity_value_type_or_order(self):
        variants = [
            [{"id": "wrong", "value": 1}, self.records[1]],
            [{"id": "alpha", "value": 999}, self.records[1]],
            [{"id": "alpha", "value": True}, self.records[1]],
            self.records[::-1],
        ]
        for values in variants:
            with self.subTest(values=values):
                receipt = save_records(self.path, self.records, writer=self.write_values(values))
                self.assertEqual(receipt["observation"]["record_count"], 2)
                self.assertEqual(receipt["observation"]["status"], "contradicted")

    def test_formatting_changes_do_not_change_content(self):
        receipt = save_records(self.path, self.records, writer=self.write_values(self.records))
        self.assertEqual(receipt["observation"]["status"], "confirmed")
        self.assertNotEqual(receipt["observation"]["file_sha256"], receipt["observation"]["content_sha256"])

    def test_unicode_separators_inside_strings_roundtrip(self):
        for separator in ("\u0085", "\u2028", "\u2029", "\n"):
            with self.subTest(separator=ascii(separator)):
                records = [{"id": "before" + separator + "after", "value": "a" + separator + "b"}]
                receipt = save_records(self.path, records)
                self.assertEqual(receipt["observation"]["status"], "confirmed")
                self.assertEqual(receipt["observation"]["record_count"], 1)
                self.assertEqual(receipt["action"]["claim"]["records"], 1)

    def test_crlf_and_optional_final_newline_are_valid_framing(self):
        text = "\r\n".join(json.dumps(record) for record in self.records)
        for suffix in ("", "\r\n"):
            with self.subTest(suffix=suffix):
                receipt = save_records(self.path, self.records,
                                       writer=self.write_bytes((text + suffix).encode()))
                self.assertEqual(receipt["observation"]["status"], "confirmed")

    def test_malformed_readbacks_are_contradicted_and_raw_hash_is_kept(self):
        variants = [b'not json\n', b'\xff', b'\n', b'null\n',
                    b'{"id":"alpha","id":"beta"}\n',
                    b'{"id":"alpha"}\n{"id":"alpha"}\n',
                    b'{"id":"alpha","value":NaN}\n']
        for payload in variants:
            with self.subTest(payload=payload):
                receipt = save_records(self.path, self.records, writer=self.write_bytes(payload))
                self.assertEqual(receipt["observation"]["status"], "contradicted")
                self.assertIsNotNone(receipt["observation"]["file_sha256"])

    def test_unavailable_readback_is_unknown_even_after_success(self):
        def unreadable(path):
            raise PermissionError("inspection unavailable")
        receipt = save_records(self.path, self.records, reader=unreadable)
        self.assertEqual(receipt["action"]["claim"]["status"], "ok")
        self.assertEqual(receipt["observation"]["status"], "unresolved")
        self.assertIsNone(receipt["observation"]["file_sha256"])

    def test_falsey_adapters_are_not_replaced_with_real_io(self):
        class Adapter:
            def __bool__(self):
                return False
            def __call__(self, *args):
                raise OSError("adapter refused")
        receipt = save_records(self.path, self.records, writer=Adapter())
        self.assertFalse(self.path.exists())
        self.assertIn("adapter refused", receipt["action"]["error"])
        receipt = save_records(self.path, self.records, reader=Adapter())
        self.assertEqual(receipt["observation"]["status"], "unresolved")
        self.assertIn("adapter refused", receipt["observation"]["reason"])

    def test_empty_state_requires_an_existing_empty_file(self):
        receipt = save_records(self.path, [])
        self.assertEqual(receipt["observation"]["status"], "confirmed")
        self.assertEqual(receipt["observation"]["record_count"], 0)
        self.assertEqual(self.path.read_bytes(), b"")

    def test_existing_state_can_be_confirmed_without_claiming_write_succeeded(self):
        save_records(self.path, self.records)
        def fail(path, data):
            raise OSError("writer failed before saving")
        receipt = save_records(self.path, self.records, writer=fail)
        self.assertEqual(receipt["observation"]["status"], "confirmed")
        self.assertIsNone(receipt["action"]["claim"])
        self.assertIn("writer failed", receipt["action"]["error"])

    def test_invalid_inputs_fail_before_any_io(self):
        cyclic = {"id": "a"}
        cyclic["value"] = cyclic
        invalid = [None, {}, [{"value": 1}], [{"id": " "}], [{"id": 1}],
                   [{"id": "a"}, {"id": "a"}], [{"id": "a", "value": float("inf")}],
                   [{"id": "a", "value": {1: "key"}}], [{"id": "a", "value": (1, 2)}], [cyclic]]
        def forbidden(*args):
            self.fail("invalid input reached I/O")
        for records in invalid:
            with self.subTest(records=records):
                with self.assertRaises(ValueError):
                    save_records(self.path, records, writer=forbidden, reader=forbidden)
        self.assertFalse(self.path.exists())

    def test_inspection_uses_requested_path_when_writer_writes_elsewhere(self):
        def elsewhere(path, data):
            (path.parent / "wrong.jsonl").write_bytes(data)
            return {"status": "ok", "records": 2}
        receipt = save_records(self.path, self.records, writer=elsewhere)
        self.assertEqual(receipt["observation"]["status"], "contradicted")


if __name__ == "__main__":
    unittest.main()
