"""Tests de contrat de bout en bout avec les cinq vrais exécutables."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from run import build_revaskel, exercise, prepare_peers


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp.cleanup)
        cls.root = Path(temp.name).resolve()
        siblings = os.environ.get("SUITE_REPOS")
        cls.peers = prepare_peers(cls.root, Path(siblings) if siblings else None)
        cls.binary = build_revaskel(cls.peers, cls.root)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name)
        source = self.peers["Mandoryve"] / "examples/group.json"
        self.mandate = json.loads(source.read_text())

    def play(self, snapshot="partial", when=6):
        mandate = self.work / "mandate.json"
        mandate.write_text(json.dumps(self.mandate))
        self.out = self.work / "out"
        return exercise(self.peers, self.binary, self.out,
                        snapshot=self.peers["Revaskel"] / "examples" / snapshot,
                        mandate=mandate, case_id="confidential-case", restore_time=when,
                        uncertainty=1, budget=2, seed=42)

    def read(self, name):
        return json.loads((self.out / name).read_text())

    def test_partial_restore_and_inherited_access(self):
        queue = self.play()
        replay = self.read("05-constats.json")
        self.assertEqual({row["result"] for row in replay["observations"]},
                         {"clear", "extra_access", "missing_document"})
        self.assertEqual(queue["population"], 3)
        self.assertEqual(len(queue["queue"]), 2)
        self.assertEqual(queue["queue"][0]["result"], "extra_access")
        self.assertEqual([row["inclusion_probability"] for row in queue["queue"]], [1, 0.5])
        ids = {row["id"] for row in self.read("03-chronologie.json")["events"]}
        for row in queue["queue"]:
            self.assertIn(row["id"], ids)
            self.assertEqual(len(row["context"]), 2)
        bundle = (self.out / "04-dossier.json").read_text()
        for private in ("DEMO-002", "confidential-case", "interne", "lea", "digest_mismatch",
                        self.read("01-restauration.json")["events"][0]["facts"]["expected"]):
            self.assertNotIn(private, bundle)
        self.assertIn({"before": "revaskel-2", "after": "mandoryve-1"}, replay["relations"])

    def test_clean_restore_and_conformant_access_with_overlapping_clocks(self):
        direct = self.mandate["after"]["direct"]
        direct.append(dict(direct[0], user="lea"))
        self.mandate["after"]["users"]["lea"] = []
        queue = self.play(snapshot="complete", when=9)
        self.assertEqual(queue["population"], 2)
        for row in queue["queue"]:
            self.assertEqual(row["result"], "clear")
            self.assertEqual(row["context"][0]["relation"], "undetermined")
            self.assertEqual(row["inclusion_probability"], 1)

    def test_unavailable_observation_survives_all_stages(self):
        del self.mandate["after"]["groups"]["support"]
        queue = self.play()
        self.assertEqual(queue["queue"][0]["result"], "unknown")
        self.assertEqual(queue["queue"][0]["id"], "mandoryve-1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
