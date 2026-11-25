import copy
import unittest

from horvessane import join_evidence


def packet(source, kind, when):
    return {"schema": "evidence.v1", "source": source, "case_id": "exercise", "events": [
        {"id": source + "-1", "kind": kind, "time_s": when, "uncertainty_s": 1, "facts": {}}]}


class JoinTests(unittest.TestCase):
    def setUp(self):
        self.a = packet("revaskel", "document", 6)
        self.b = packet("mandoryve", "verified", 10)

    def test_orders_only_disjoint_windows(self):
        report = join_evidence([self.a, self.b])
        self.assertEqual(report["timeline"]["relations"][0]["before"], "revaskel-1")
        self.b["events"][0]["time_s"] = 8
        self.assertIn("undetermined", join_evidence([self.a, self.b])["timeline"]["relations"][0])

    def test_mixed_case_missing_source_and_protocol_rejected(self):
        with self.assertRaises(ValueError):
            join_evidence([self.a])
        for field, value in (("case_id", "other"), ("schema", "v9"), ("source", "revaskel")):
            wrong = copy.deepcopy(self.b)
            wrong[field] = value
            with self.assertRaises(ValueError):
                join_evidence([self.a, wrong])
