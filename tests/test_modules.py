import unittest

from generation import build_grounded_prompt, citation_block
from ingestion import chunk_text, prepare_unique_chunks
from retrieval import distance_to_relevance, hybrid_score, lexical_overlap_score


class TestLearningModules(unittest.TestCase):
    def test_chunking_and_deduplication(self):
        chunks = chunk_text("abcdefghij", chunk_size=6, chunk_overlap=2)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(len(prepare_unique_chunks(chunks + [chunks[0]])), len(chunks))

    def test_retrieval_scoring(self):
        self.assertGreater(lexical_overlap_score("coffee", "coffee tea"), 0)
        self.assertEqual(distance_to_relevance(0), 1.0)
        self.assertAlmostEqual(hybrid_score(1.0, 0.0, 0.75, 0.25), 0.75)

    def test_grounded_prompt_and_citation(self):
        data = build_grounded_prompt("What is the date?", [{
            "document": "The date is 1 January 2568.",
            "metadata": {"source": "sample.txt"},
            "final_score": 0.9,
        }])
        self.assertIn("Context:", data["prompt"])
        self.assertIn("Question: What is the date?", data["prompt"])
        self.assertEqual(data["sources"], ["sample.txt"])
        self.assertIn("sample.txt", citation_block(data["sources"]))


if __name__ == "__main__":
    unittest.main()
