"""Real caption-level POS regressions remain independent of fact extraction."""
import unittest
from decomposition.pos_parser import SpacyParser

class PosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = SpacyParser()

    def test_counts_real_pipeline(self):
        counts, sentences = self.parser.parse("Two red cats sit under a table.")
        self.assertEqual(counts, {"NOUN_count": 2, "ADJ_count": 1, "VERB_count": 1, "ADP_count": 1, "NUM_count": 1})
        self.assertEqual(sentences, 1)

    def test_empty_counts(self):
        counts, sentences = self.parser.parse("")
        self.assertTrue(all(value == 0 for value in counts.values()))
        self.assertEqual(sentences, 0)


if __name__ == "__main__":
    unittest.main()
