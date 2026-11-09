"""Predeclared synthetic clustering metrics, never used by application inference."""

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from productlens.grouping import normalise_text


def pair_metrics(truth, predicted, texts, nonidentical_only=False) -> dict:
    """Unordered clear-row pairs; exact normalised text can be excluded."""
    truth, predicted, texts = np.asarray(truth), np.asarray(predicted), np.asarray(texts)
    left, right = np.triu_indices(len(truth), k=1)
    if nonidentical_only:
        keep = texts[left] != texts[right]
        left, right = left[keep], right[keep]
    positive = truth[left] == truth[right]
    proposed = predicted[left] == predicted[right]
    tp = int(np.sum(positive & proposed))
    fp = int(np.sum(~positive & proposed))
    fn = int(np.sum(positive & ~proposed))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
    return {"pair_count": len(left), "true_positive": tp, "false_positive": fp,
            "false_negative": fn, "precision": precision, "recall": recall, "f1": f1}


def clustering_metrics(evidence: pd.DataFrame, assignments: pd.DataFrame) -> dict:
    if not assignments.feedback_id.is_unique or set(evidence.feedback_id) != set(assignments.feedback_id):
        raise ValueError("Predictions must cover each evidence ID exactly once.")
    joined = evidence.merge(assignments, on="feedback_id", validate="one_to_one")
    clear = joined[joined.eligible_single_theme & joined.eligible_duplicate].copy()
    clear["normalised_text"] = clear.feedback_text.map(normalise_text)
    if clear.groupby("normalised_text").primary_theme.nunique().gt(1).any():
        raise ValueError("Identical text has conflicting theme labels.")
    if clear.groupby("normalised_text").duplicate_group.nunique().gt(1).any():
        raise ValueError("Identical text has conflicting duplicate labels.")
    output = {"total_rows": len(joined), "eligible_rows": len(clear),
              "excluded_challenge_rows": len(joined) - len(clear)}
    for name, frame in (("rows", clear), ("unique_texts", clear.drop_duplicates("normalised_text"))):
        output[name] = {
            "count": len(frame), "opportunity_groups": int(frame.opportunity_id.nunique()),
            "theme_ari": float(adjusted_rand_score(frame.primary_theme, frame.opportunity_id)) if len(frame) > 1 else None,
            "theme_nmi": float(normalized_mutual_info_score(frame.primary_theme, frame.opportunity_id, average_method="arithmetic")) if len(frame) > 1 else None,
            "duplicate_pairs": pair_metrics(frame.duplicate_group, frame.duplicate_group_id, frame.normalised_text),
            "nonidentical_duplicate_pairs": pair_metrics(frame.duplicate_group, frame.duplicate_group_id,
                                                         frame.normalised_text, nonidentical_only=True),
        }
    return output
