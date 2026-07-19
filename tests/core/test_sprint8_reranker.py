import sys
import math
import unittest
from unittest.mock import MagicMock, patch

# Mock sentence_transformers module globally before imports run
mock_sentence_transformers = MagicMock()
mock_cross_encoder_class = MagicMock()
mock_sentence_transformers.CrossEncoder = mock_cross_encoder_class
sys.modules["sentence_transformers"] = mock_sentence_transformers

from config import settings
from core.di import DIContainer
from core.di_setup import bootstrap_di
from core.context.reranker import IReranker
from core.context.cross_encoder_reranker import CrossEncoderReranker
from core.schemas import RetrievedCodeChunk


class TestCrossEncoderReranker(unittest.TestCase):
    def setUp(self) -> None:
        # Reset DIContainer and bootstrap
        DIContainer.clear()
        bootstrap_di()

        # Reset mocks
        mock_cross_encoder_class.reset_mock()
        mock_cross_encoder_class.side_effect = None

        # Backup settings
        self._backup_enabled = settings.reranker_enabled
        self._backup_model = settings.reranker_model
        self._backup_top_k = settings.rerank_top_k
        self._backup_threshold = settings.rerank_score_threshold
        self._backup_batch_size = settings.rerank_batch_size
        self._backup_device = settings.rerank_device

    def tearDown(self) -> None:
        # Restore settings
        settings.reranker_enabled = self._backup_enabled
        settings.reranker_model = self._backup_model
        settings.rerank_top_k = self._backup_top_k
        settings.rerank_score_threshold = self._backup_threshold
        settings.rerank_batch_size = self._backup_batch_size
        settings.rerank_device = self._backup_device

    def test_di_registration(self) -> None:
        """
        Verify that IReranker and CrossEncoderReranker are registered correctly.
        """
        reranker = DIContainer.get(IReranker)
        self.assertIsInstance(reranker, CrossEncoderReranker)

    def test_disabled_mode(self) -> None:
        """
        Verify that when disabled, the reranker does not load the model or perform inference,
        and returns the original candidates completely unchanged.
        """
        settings.reranker_enabled = False
        reranker = CrossEncoderReranker()

        chunks = [
            RetrievedCodeChunk(
                file_path="a.py",
                content="content a",
                score=0.5,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="b.py",
                content="content b",
                score=0.8,
                start_line=1,
                end_line=10,
            ),
        ]

        result = reranker.rerank("query", chunks)
        self.assertEqual(result, chunks)
        self.assertIsNone(reranker._model)
        self.assertFalse(reranker.health_check())
        mock_cross_encoder_class.assert_not_called()

    def test_lazy_loading(self) -> None:
        """
        Verify that CrossEncoder model is only loaded on the first rerank() invocation.
        """
        settings.reranker_enabled = True

        reranker = CrossEncoderReranker()
        self.assertIsNone(reranker._model)

        mock_model_instance = MagicMock()
        mock_model_instance.predict.return_value = [0.0, 1.0]
        mock_cross_encoder_class.return_value = mock_model_instance

        chunks = [
            RetrievedCodeChunk(
                file_path="a.py",
                content="content a",
                score=0.5,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="b.py",
                content="content b",
                score=0.8,
                start_line=1,
                end_line=10,
            ),
        ]

        # First invocation loading model
        result = reranker.rerank("query", chunks)
        self.assertIsNotNone(reranker._model)
        mock_cross_encoder_class.assert_called_once()
        self.assertTrue(reranker.health_check())

        # Second invocation reusing the cached model
        _ = reranker.rerank("query", chunks)
        mock_cross_encoder_class.assert_called_once()

    def test_score_normalization_and_sorting(self) -> None:
        """
        Verify that raw logits are normalized into probability values via sigmoid,
        and sorted in descending order of normalized scores.
        """
        settings.reranker_enabled = True
        settings.rerank_score_threshold = 0.0
        settings.rerank_top_k = 5

        reranker = CrossEncoderReranker()

        mock_model_instance = MagicMock()
        # Mock logits: 2.0 (sigmoid ~0.88), -2.0 (sigmoid ~0.12), 0.0 (sigmoid 0.5)
        mock_model_instance.predict.return_value = [2.0, -2.0, 0.0]
        mock_cross_encoder_class.return_value = mock_model_instance

        chunks = [
            RetrievedCodeChunk(
                file_path="a.py",
                content="content a",
                score=0.1,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="b.py",
                content="content b",
                score=0.2,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="c.py",
                content="content c",
                score=0.3,
                start_line=1,
                end_line=10,
            ),
        ]

        result = reranker.rerank("query", chunks)

        # Expected output order: a (0.88), c (0.5), b (0.12)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].file_path, "a.py")
        self.assertAlmostEqual(result[0].score, 1.0 / (1.0 + math.exp(-2.0)))

        self.assertEqual(result[1].file_path, "c.py")
        self.assertAlmostEqual(result[1].score, 0.5)

        self.assertEqual(result[2].file_path, "b.py")
        self.assertAlmostEqual(result[2].score, 1.0 / (1.0 + math.exp(2.0)))

    def test_threshold_filtering(self) -> None:
        """
        Verify that candidate chunks below settings.rerank_score_threshold are filtered out.
        """
        settings.reranker_enabled = True
        settings.rerank_score_threshold = 0.5
        settings.rerank_top_k = 5

        reranker = CrossEncoderReranker()

        mock_model_instance = MagicMock()
        # Logits: 1.0 (sigmoid ~0.73), -1.0 (sigmoid ~0.27)
        mock_model_instance.predict.return_value = [1.0, -1.0]
        mock_cross_encoder_class.return_value = mock_model_instance

        chunks = [
            RetrievedCodeChunk(
                file_path="a.py",
                content="content a",
                score=0.1,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="b.py",
                content="content b",
                score=0.2,
                start_line=1,
                end_line=10,
            ),
        ]

        result = reranker.rerank("query", chunks)

        # Only 'a' has score >= 0.5
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_path, "a.py")

    def test_batching_and_top_k(self) -> None:
        """
        Verify that predictions are batched according to config and output is capped by top-k.
        """
        settings.reranker_enabled = True
        settings.rerank_score_threshold = 0.0
        settings.rerank_top_k = 2
        settings.rerank_batch_size = 4

        reranker = CrossEncoderReranker()

        mock_model_instance = MagicMock()
        mock_model_instance.predict.return_value = [0.0, 1.0, 2.0]
        mock_cross_encoder_class.return_value = mock_model_instance

        chunks = [
            RetrievedCodeChunk(
                file_path="a.py",
                content="content a",
                score=0.1,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="b.py",
                content="content b",
                score=0.2,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="c.py",
                content="content c",
                score=0.3,
                start_line=1,
                end_line=10,
            ),
        ]

        result = reranker.rerank("query", chunks)

        # Capped at top_k = 2
        self.assertEqual(len(result), 2)
        mock_model_instance.predict.assert_called_once_with(
            [
                ["query", "content a"],
                ["query", "content b"],
                ["query", "content c"],
            ],
            batch_size=4,
            show_progress_bar=False,
        )

    def test_telemetry_generation(self) -> None:
        """
        Verify that execution telemetry is correctly recorded in history.
        """
        settings.reranker_enabled = True
        settings.rerank_score_threshold = 0.5
        settings.rerank_top_k = 5

        reranker = CrossEncoderReranker()

        mock_model_instance = MagicMock()
        mock_model_instance.predict.return_value = [1.0, -1.0]
        mock_cross_encoder_class.return_value = mock_model_instance

        chunks = [
            RetrievedCodeChunk(
                file_path="a.py",
                content="content a",
                score=0.1,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="b.py",
                content="content b",
                score=0.2,
                start_line=1,
                end_line=10,
            ),
        ]

        _ = reranker.rerank("query", chunks)

        self.assertEqual(len(reranker.telemetry_history), 1)
        telemetry = reranker.telemetry_history[0]
        self.assertIn("model_load_time", telemetry)
        self.assertIn("rerank_latency", telemetry)
        self.assertEqual(telemetry["batch_size"], settings.rerank_batch_size)
        self.assertEqual(telemetry["candidate_count"], 2)
        self.assertEqual(telemetry["filtered_count"], 1)
        self.assertGreater(telemetry["average_confidence"], 0.0)

    def test_error_handling_fallback(self) -> None:
        """
        Verify that any model loading/prediction error is gracefully handled
        by warning logging, recording error telemetry, and returning original chunks.
        """
        settings.reranker_enabled = True

        reranker = CrossEncoderReranker()

        # Simulate loader failure
        mock_cross_encoder_class.side_effect = RuntimeError("CUDA Out of Memory")

        chunks = [
            RetrievedCodeChunk(
                file_path="a.py",
                content="content a",
                score=0.1,
                start_line=1,
                end_line=10,
            ),
            RetrievedCodeChunk(
                file_path="b.py",
                content="content b",
                score=0.2,
                start_line=1,
                end_line=10,
            ),
        ]

        result = reranker.rerank("query", chunks)
        # Should gracefully return original chunks
        self.assertEqual(result, chunks)

        # Check telemetry recorded the error
        self.assertEqual(len(reranker.telemetry_history), 1)
        self.assertIn("error", reranker.telemetry_history[0])
        self.assertEqual(
            reranker.telemetry_history[0]["error"], "CUDA Out of Memory"
        )
