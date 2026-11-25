import unittest

from horvessane import analyze


def case(times=(1, 2, 3), error=4):
    return {"events": [dict(id=key, time_s=t, uncertainty_s=error)
                       for key, t in zip("abc", times)], "anchors": []}


def anchor(a, b):
    return dict(before=a, after=b, evidence=f"trace {a}/{b}")


class OrderTests(unittest.TestCase):
    def test_overlap_is_undetermined(self):
        self.assertEqual(len([p for p in analyze(case())["relations"] if "undetermined" in p]), 3)

    def test_transitive_evidence(self):
        data = case()
        data["anchors"] = [anchor("a", "b"), anchor("b", "c")]
        inferred = analyze(data)["relations"][1]
        self.assertEqual((inferred["before"], inferred["after"], len(inferred["evidence"])), ("a", "c", 2))

    def test_disjoint_intervals_and_contradictory_anchor(self):
        data = case(error=0)
        self.assertEqual(analyze(data)["relations"][0]["before"], "a")
        data["anchors"] = [anchor("c", "a")]
        self.assertEqual(analyze(data)["status"], "contradiction")

    def test_touching_bounds_are_ambiguous(self):
        self.assertIn("undetermined", analyze(case((0, 2, 4), 1))["relations"][0])

    def test_invalid_anchor(self):
        data = case()
        data["anchors"] = [anchor("a", "x")]
        with self.assertRaises(ValueError):
            analyze(data)

    def test_strict_order_at_same_exact_instant(self):
        data = case((1, 1, 2), 0)
        data["anchors"] = [anchor("a", "b")]
        self.assertEqual(analyze(data)["status"], "contradiction")
