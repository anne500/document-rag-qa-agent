"""Offline whole-ID ranking and paired-runner tests; no model calls."""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import eval_id_retrieval as runner
from id_retrieval import IdentifierAwareRetriever, IdentifierIndex, candidate, chunk_key, identifiers


def chunk(source, text, page=None, distance=None):
    metadata = {"source": source}
    if page is not None:
        metadata["page"] = page
    return candidate(text, metadata, distance)


class IdentifierTests(unittest.TestCase):
    def test_case_insensitive_ids_release_labels_and_query_order(self):
        self.assertEqual(
            identifiers("(maple-207), ATLAS-R12 and MAPLE-207 then CEDAR-104."),
            ["MAPLE-207", "ATLAS-R12", "CEDAR-104"],
        )

    def test_complete_tokens_not_prefixes_or_embedded_ids(self):
        items = identifiers("MAPLE-2070 MAPLE-207x prefix_MAPLE-207 MAPLE-207-extra")
        self.assertNotIn("MAPLE-207", items)
        self.assertIn("MAPLE-2070", items)

    def test_no_identifier_for_normal_hyphenated_words(self):
        self.assertEqual(identifiers("release-ready cedar-utils cloud-provider"), [])

    def test_ascii_hyphens_only(self):
        self.assertEqual(identifiers("MAPLE\u2011207"), [])


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.birch = chunk("birch.md", "BIRCH-309 ran out of disk space.", distance=0.1)
        self.maple = chunk("maple.md", "MAPLE-207 failed because its certificate expired.")
        self.cedar = chunk("cedar.md", "CEDAR-104 cannot resolve a dependency.")
        self.inventory = [self.birch, self.maple, self.cedar]
        self.index = IdentifierIndex(self.inventory)

    def test_exact_id_promoted_even_outside_semantic_pool(self):
        ranked, trace = self.index.rerank(
            "Did MAPLE-207 run out of disk space?", [self.birch]
        )
        self.assertEqual(ranked[0]["source"], "maple.md")
        self.assertIsNone(ranked[0]["distance"])
        self.assertIsNone(ranked[0]["semantic_rank"])
        self.assertEqual(trace["matched_ids"], ["MAPLE-207"])

    def test_no_id_preserves_semantic_order_and_input_is_not_mutated(self):
        before = copy.deepcopy(self.inventory)
        ranked, trace = self.index.rerank("Who approves releases?", self.inventory)
        self.assertEqual([chunk_key(c) for c in ranked],
                         [chunk_key(c) for c in self.inventory])
        self.assertEqual(trace["policy"], "semantic_fallback")
        self.assertEqual(before, self.inventory)

    def test_unknown_id_preserves_semantic_order(self):
        ranked, trace = self.index.rerank("Why did MAPLE-2070 fail?", self.inventory)
        self.assertEqual(ranked[0]["source"], "birch.md")
        self.assertEqual(trace["unknown_ids"], ["MAPLE-2070"])
        self.assertEqual(trace["matched_ids"], [])

    def test_multiple_known_ids_get_one_leading_chunk_each(self):
        extra = chunk("maple.md", "MAPLE-207 has additional details.")
        index = IdentifierIndex(self.inventory + [extra])
        ranked, _ = index.rerank("Compare MAPLE-207 and CEDAR-104", [extra, self.maple, self.birch])
        self.assertEqual([c["source"] for c in ranked[:2]], ["maple.md", "cedar.md"])

    def test_mixed_known_and_unknown_ids_are_reported(self):
        ranked, trace = self.index.rerank("MAPLE-207 and UNKNOWN-99", [self.birch])
        self.assertEqual(ranked[0]["source"], "maple.md")
        self.assertEqual(trace["unknown_ids"], ["UNKNOWN-99"])

    def test_exact_candidate_keeps_semantic_distance_and_rank_when_present(self):
        ranked, _ = self.index.rerank("MAPLE-207?", [self.birch, {**self.maple, "distance": 0.3}])
        self.assertEqual(ranked[0]["distance"], 0.3)
        self.assertEqual(ranked[0]["semantic_rank"], 2)

    def test_same_source_page_and_text_deduplicated_in_priority_mode(self):
        ranked, _ = self.index.rerank("MAPLE-207?", [self.maple, self.maple, self.birch])
        self.assertEqual(len({chunk_key(c) for c in ranked}), len(ranked))
        self.assertEqual(len(ranked), 2)

    def test_page_identity_is_preserved(self):
        first = chunk("atlas.pdf", "ATLAS-418 details.", page=1)
        second = chunk("atlas.pdf", "ATLAS-418 details.", page=2)
        ranked, _ = IdentifierIndex([first, second]).rerank("ATLAS-418", [second, first])
        self.assertEqual([c["page"] for c in ranked], [2, 1])

    def test_inventory_order_does_not_change_lexical_fallback_ties(self):
        other = chunk("maple-notes.md", "MAPLE-207 is mentioned here.")
        query = "MAPLE-207"
        a, _ = IdentifierIndex([self.maple, other]).rerank(query, [])
        b, _ = IdentifierIndex([other, self.maple]).rerank(query, [])
        self.assertEqual([chunk_key(c) for c in a], [chunk_key(c) for c in b])


class AdapterTests(unittest.TestCase):
    def test_adapter_reads_inventory_once_and_caps_pool(self):
        class Store:
            reads = 0
            requested = []

            def get(self, include):
                self.reads += 1
                return {
                    "documents": ["BIRCH-309 disk full", "MAPLE-207 certificate expired"],
                    "metadatas": [{"source": "birch.md"}, {"source": "maple.md"}],
                }

            def similarity_search_with_score(self, question, k):
                self.requested.append(k)
                return [(SimpleNamespace(
                    page_content="BIRCH-309 disk full", metadata={"source": "birch.md"}
                ), 0.1)]

        store = Store()
        retriever = IdentifierAwareRetriever(store, candidate_pool=20)
        first = retriever.retrieve("MAPLE-207?", k=1)
        retriever.retrieve("unknown question", k=1)
        self.assertEqual(first["ranked"][0]["source"], "maple.md")
        self.assertEqual(store.reads, 1)
        self.assertEqual(store.requested, [2, 2])

    def test_invalid_k_pool_or_missing_source_rejected(self):
        with self.assertRaises(ValueError):
            IdentifierAwareRetriever(object(), candidate_pool=0)
        with self.assertRaises(ValueError):
            candidate("text", {})
        class Store:
            def get(self, **kwargs):
                return {"documents": ["text"], "metadatas": []}
        with self.assertRaises(ValueError):
            IdentifierAwareRetriever(Store())


class PairedRunnerTests(unittest.TestCase):
    def run_fixture(self, failure=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        doc = SimpleNamespace(
            page_content="MAPLE-207 certificate expired.", metadata={"source": "maple.md"}
        )
        sample = {
            "schema_version": 1, "expected_sources": ["maple.md"],
            "expected_document_units": 1,
            "cases": [
                {"id": "maple", "kind": "evidence", "question": "MAPLE-207?",
                 "required_evidence": [{"id": "certificate", "source": "maple.md",
                                        "page": None, "contains": ["certificate", "expired"]}]},
                {"id": "control", "kind": "no_evidence",
                 "question": "Absent information?", "required_evidence": []},
            ],
        }
        path = root / "cases.json"
        path.write_text(json.dumps(sample))
        for name in ["eval_id_retrieval.py", "id_retrieval.py", "eval_retrieval.py",
                     "retrieval_metrics.py", "qa_agent.py"]:
            (root / name).write_text("# offline fixture")

        class Splitter:
            def __init__(self, **kwargs):
                pass
            def split_documents(self, documents):
                return documents

        class Store:
            deleted = 0
            @classmethod
            def from_documents(cls, **kwargs):
                return cls()
            def similarity_search_with_score(self, question, k):
                if failure and question == "Absent information?":
                    raise failure
                return [(doc, 0.1)]
            def delete_collection(self):
                Store.deleted += 1

        modules = {
            "qa_agent": SimpleNamespace(load_documents=lambda: [doc]),
            "langchain_chroma": SimpleNamespace(Chroma=Store),
            "langchain_ollama": SimpleNamespace(OllamaEmbeddings=lambda **kwargs: object()),
            "langchain_text_splitters": SimpleNamespace(RecursiveCharacterTextSplitter=Splitter),
        }
        with patch.object(runner, "ROOT", root), patch.dict("sys.modules", modules), \
             patch.object(runner.lab, "model_identity", return_value={"digest": "offline"}), \
             patch.object(runner, "version", return_value="offline"), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = runner.main(["--cases", str(path), "--chunk-sizes", "500", "--ks", "1", "2"])
        directory = next((root / "verification" / "identifier-runs").iterdir())
        report = json.loads((directory / "report.json").read_text())
        return code, directory, report, Store.deleted

    def test_complete_run_records_both_methods_and_lf_csv(self):
        code, directory, report, deleted = self.run_fixture()
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(len(runner.summary_rows(report)), 4)
        self.assertEqual(len(runner.paired_rows(report)), 2)
        self.assertNotIn(b"\r", (directory / "metrics.csv").read_bytes())
        self.assertTrue((directory / "semantic-results.svg").is_file())
        self.assertTrue((directory / "id_priority-results.svg").is_file())
        self.assertEqual(deleted, 1)

    def test_failure_retains_pair_without_complete_aggregate(self):
        code, _, report, deleted = self.run_fixture(RuntimeError("offline failure"))
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(len(report["configurations"][0]["cases"]), 1)
        self.assertEqual(runner.summary_rows(report), [])
        self.assertEqual(deleted, 1)

    def test_interrupted_pair_run_preserves_actual_status(self):
        code, _, report, deleted = self.run_fixture(KeyboardInterrupt())
        self.assertEqual(code, 130)
        self.assertEqual(report["status"], "interrupted")
        self.assertEqual(deleted, 1)

    def test_paired_deltas_preserve_negative_results(self):
        _, _, report, _ = self.run_fixture()
        score = report["configurations"][0]["cases"][0]["strategies"]["id_priority"]["scores_by_k"]["1"]
        score["complete_at_k"] = 0
        first = runner.paired_rows(report)[0]
        self.assertEqual(first["complete_at_k_delta"], -1)


if __name__ == "__main__":
    unittest.main()
