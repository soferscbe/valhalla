"""Deterministic, evidence-linked clustering; no label catalog or ranking input."""

from dataclasses import dataclass
import hashlib

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer

from productlens.embeddings import encode_texts
from productlens.ingestion import validate_feedback

MAX_GROUPING_ROWS = 2000


@dataclass(frozen=True)
class GroupingConfig:
    opportunity_similarity: float
    duplicate_similarity: float

    def __post_init__(self):
        if not (0 < self.opportunity_similarity <= self.duplicate_similarity < 1):
            raise ValueError("Similarity thresholds must satisfy 0 < opportunity <= duplicate < 1.")


@dataclass
class PreparedFeedback:
    data: pd.DataFrame
    texts: list[str]
    row_to_unique: np.ndarray
    embeddings: np.ndarray
    truncated: list[bool]


@dataclass
class GroupingResult:
    assignments: pd.DataFrame
    opportunities: pd.DataFrame


def normalise_text(text: str) -> str:
    return " ".join(text.casefold().split())


def prepare_feedback(frame: pd.DataFrame, encoder=None) -> PreparedFeedback:
    if len(frame) > MAX_GROUPING_ROWS:
        raise ValueError(f"Semantic grouping supports at most {MAX_GROUPING_ROWS:,} rows per run.")
    # Explicitly accept a schema-valid empty frame for pipeline use.
    if frame.empty and all(c in frame for c in ("feedback_id", "customer_id", "feedback_text")):
        return PreparedFeedback(frame.copy(), [], np.array([], dtype=int), np.empty((0, 384)), [])
    validation = validate_feedback(frame)
    if not validation.valid:
        raise ValueError("Cannot group invalid feedback: " + "; ".join(validation.errors))
    data = validation.data.sort_values("feedback_id").reset_index(drop=True)
    normalised = data.feedback_text.map(normalise_text)
    texts = sorted(set(normalised))
    positions = {text: index for index, text in enumerate(texts)}
    vectors, truncated = (encoder or encode_texts)(texts)
    vectors = np.asarray(vectors, dtype=np.float64)
    if (vectors.ndim != 2 or vectors.shape[0] != len(texts) or vectors.shape[1] == 0
            or not np.isfinite(vectors).all() or len(truncated) != len(texts)):
        raise ValueError("Encoder returned invalid embeddings or truncation flags.")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if (norms <= 0).any():
        raise ValueError("Encoder returned zero-length vectors.")
    return PreparedFeedback(data, texts, normalised.map(positions).to_numpy(dtype=int),
                            vectors / norms, list(truncated))


def _clusters(vectors: np.ndarray, similarity: float) -> np.ndarray:
    if len(vectors) < 2:
        return np.zeros(len(vectors), dtype=int)
    distances = np.clip(1 - vectors @ vectors.T, 0, 2)
    np.fill_diagonal(distances, 0)
    return AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage="complete",
                                   distance_threshold=1 - similarity).fit_predict(distances)


def _ids(labels: np.ndarray, texts: list[str], prefix: str) -> dict[int, str]:
    return {int(label): prefix + hashlib.sha256("\n".join(
        texts[index] for index in np.flatnonzero(labels == label)
    ).encode()).hexdigest()[:12] for label in np.unique(labels)}


def _terms(texts: list[str], labels: np.ndarray) -> dict[int, str]:
    if not texts:
        return {}
    try:
        vectoriser = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        matrix = vectoriser.fit_transform(texts)
        words = vectoriser.get_feature_names_out()
        output = {}
        for label in np.unique(labels):
            scores = np.asarray(matrix[labels == label].mean(axis=0)).ravel()
            top = sorted(range(len(words)), key=lambda index: (-scores[index], words[index]))[:3]
            output[int(label)] = ", ".join(words[index] for index in top if scores[index] > 0)
        return output
    except ValueError:  # All stop words / punctuation: retain the source representative.
        return {int(label): "" for label in np.unique(labels)}


def group_prepared(prepared: PreparedFeedback, config: GroupingConfig) -> GroupingResult:
    data, vectors = prepared.data, prepared.embeddings
    assignment_columns = ["feedback_id", "opportunity_id", "duplicate_group_id", "similarity_to_representative", "text_truncated"]
    opportunity_columns = ["opportunity_id", "representative_feedback_id", "representative_request", "key_terms",
                           "request_count", "distinct_customers", "unique_wordings", "duplicate_groups",
                           "minimum_similarity", "review_note"]
    if data.empty:
        return GroupingResult(pd.DataFrame(columns=assignment_columns), pd.DataFrame(columns=opportunity_columns))
    broad = _clusters(vectors, config.opportunity_similarity)
    strict = _clusters(vectors, config.duplicate_similarity)
    opportunity_ids, duplicate_ids = _ids(broad, prepared.texts, "O-"), _ids(strict, prepared.texts, "D-")
    terms = _terms(prepared.texts, broad)
    assignments = data[["feedback_id"]].copy()
    assignments["opportunity_id"] = [opportunity_ids[int(broad[i])] for i in prepared.row_to_unique]
    assignments["duplicate_group_id"] = [duplicate_ids[int(strict[i])] for i in prepared.row_to_unique]
    assignments["similarity_to_representative"] = 0.0
    assignments["text_truncated"] = [prepared.truncated[i] for i in prepared.row_to_unique]
    opportunities = []
    for label in np.unique(broad):
        unique_indices = np.flatnonzero(broad == label)
        similarities = vectors[unique_indices] @ vectors[unique_indices].T
        medoid = unique_indices[int(np.argmax(similarities.mean(axis=1)))]
        member_mask = np.isin(prepared.row_to_unique, unique_indices)
        member_rows = data.loc[member_mask]
        representative = data.iloc[int(np.flatnonzero(prepared.row_to_unique == medoid)[0])]
        assignments.loc[member_mask, "similarity_to_representative"] = np.clip(
            vectors[prepared.row_to_unique[member_mask]] @ vectors[medoid], -1, 1)
        opportunities.append({
            "opportunity_id": opportunity_ids[int(label)],
            "representative_feedback_id": representative.feedback_id,
            "representative_request": representative.feedback_text,
            "key_terms": terms[int(label)], "request_count": len(member_rows),
            "distinct_customers": int(member_rows.customer_id.nunique()),
            "unique_wordings": len(unique_indices),
            "duplicate_groups": int(np.unique(strict[unique_indices]).size),
            "minimum_similarity": float(np.clip(similarities.min(), -1, 1)),
            "review_note": "One distinct wording; validate the need." if len(unique_indices) == 1
                           else "Check shared need, scope and possible multiple intents.",
        })
    return GroupingResult(assignments[assignment_columns], pd.DataFrame(opportunities, columns=opportunity_columns)
                          .sort_values("opportunity_id").reset_index(drop=True))


def group_feedback(frame: pd.DataFrame, config: GroupingConfig, encoder=None) -> GroupingResult:
    return group_prepared(prepare_feedback(frame, encoder), config)
