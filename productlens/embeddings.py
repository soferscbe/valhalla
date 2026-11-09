"""Pinned local CPU embeddings. Model download sends no feedback to a service."""

from functools import lru_cache
import os
from pathlib import Path

import numpy as np

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MAX_TOKENS = 256
CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache" / "models"
MODEL_FILES = [
    "config.json", "config_sentence_transformers.json", "modules.json",
    "sentence_bert_config.json", "special_tokens_map.json", "tokenizer.json",
    "tokenizer_config.json", "vocab.txt", "1_Pooling/config.json", "model.safetensors",
]


class EmbeddingUnavailable(RuntimeError):
    """Model loading/encoding failed; there is no lexical substitute."""


@lru_cache(maxsize=1)
def load_model():
    try:
        from huggingface_hub import snapshot_download
        from sentence_transformers import SentenceTransformer
        import torch

        arguments = dict(repo_id=MODEL_ID, revision=MODEL_REVISION,
                         cache_dir=str(CACHE_DIR), allow_patterns=MODEL_FILES, token=False)
        try:
            snapshot = snapshot_download(**arguments, local_files_only=True)
            if not all((Path(snapshot) / name).is_file() for name in MODEL_FILES):
                raise FileNotFoundError("Incomplete model cache")
        except (OSError, ValueError):
            if os.environ.get("PRODUCTLENS_OFFLINE") == "1":
                raise
            snapshot = snapshot_download(**arguments)
        torch.set_num_threads(2)
        model = SentenceTransformer(snapshot, device="cpu", local_files_only=True,
                                    trust_remote_code=False, model_kwargs={"use_safetensors": True})
        model.max_seq_length = MAX_TOKENS
        model.eval()
        return model
    except Exception as exc:
        raise EmbeddingUnavailable(
            "The semantic model could not be loaded. Check the first-download connection "
            "and model cache, then retry. Feedback has not been sent to an external AI service."
        ) from exc


def encode_texts(texts: list[str]) -> tuple[np.ndarray, list[bool]]:
    if not texts:
        return np.empty((0, 384), dtype=np.float32), []
    model = load_model()
    try:
        token_ids = model.tokenizer(texts, truncation=False, padding=False)["input_ids"]
        truncated = [len(ids) > MAX_TOKENS for ids in token_ids]
        vectors = model.encode(texts, batch_size=32, show_progress_bar=False,
                               convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32), truncated
    except Exception as exc:
        raise EmbeddingUnavailable("Semantic encoding failed. Retry with a smaller batch of feedback.") from exc


if __name__ == "__main__":
    model = load_model()
    print(f"Ready: {MODEL_ID}@{MODEL_REVISION}; CPU; {model.get_embedding_dimension()} dimensions")
