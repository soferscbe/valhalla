"""Seeded synthetic evidence bundles. Run: python -m productlens.synthetic --help.

No labels or generation metadata are added to feedback/model-input files. See
docs/SYNTHETIC_DATA.md for split rules, signal meanings and research limitations.
"""

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import platform
import random

import pandas as pd

from productlens.ingestion import OPTIONAL, REQUIRED, validate_feedback
from productlens.synthetic_catalog import FAMILIES, Family

DATASET_VERSION = "1.0.0"
START_DATE = date(2026, 7, 8)
END_DATE = date(2026, 11, 4)
SPLITS = ("tuning", "evaluation")
THEME_WEIGHTS = {
    "reporting": 18, "audit_history": 8, "identity_access": 8,
    "dashboard_customisation": 30, "usage_alerts": 16, "bulk_editing": 20,
}
# Baselines in person-days; individual family estimates vary by 0–3 days.
EFFORT = {"reporting": 4, "audit_history": 9, "identity_access": 14,
          "dashboard_customisation": 1, "usage_alerts": 5, "bulk_editing": 4}
SEGMENTS = ("Startup", "SMB", "Enterprise")
ARR_RANGES = {"Startup": (120, 1800), "SMB": (2400, 12000), "Enterprise": (24000, 120000)}


@dataclass(frozen=True)
class GenerationConfig:
    rows: int = 500
    seed: int = 42

    def __post_init__(self):
        if type(self.rows) is not int or not 200 <= self.rows <= 10_000:
            raise ValueError("rows must be an integer between 200 and 10,000.")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be an integer between 0 and 2**32 - 1.")


@dataclass
class SyntheticDataset:
    config: GenerationConfig
    feedback: pd.DataFrame
    labels: pd.DataFrame
    customers: pd.DataFrame

    def feedback_for(self, split: str) -> pd.DataFrame:
        if split not in SPLITS:
            raise ValueError(f"split must be one of {SPLITS}.")
        ids = set(self.labels.loc[self.labels.split == split, "feedback_id"])
        return self.feedback[self.feedback.feedback_id.isin(ids)].copy()

    def model_input(self, split: str) -> pd.DataFrame:
        """IDs are join keys only. Embed feedback_text, never IDs/business/truth."""
        return self.feedback_for(split)[["feedback_id", "feedback_text"]].copy()


def _allocate(total: int, weights: dict[str, int]) -> dict[str, int]:
    """Largest-remainder allocation, with lexical ties, preserving exact size."""
    denominator = sum(weights.values())
    counts = {key: total * weight // denominator for key, weight in weights.items()}
    order = sorted(weights, key=lambda key: (-(total * weights[key] % denominator), key))
    for key in order[:total - sum(counts.values())]:
        counts[key] += 1
    return counts


def _family_splits(rng: random.Random) -> dict[str, str]:
    # Partition entire semantic intents, not just alternative phrasings. Same
    # themes are intentionally present in both halves of this controlled study.
    result = {}
    for category in (*THEME_WEIGHTS, "overlapping", "ambiguous"):
        group = [f.key for f in FAMILIES
                 if (f.themes[0] if f.kind == "clear" else f.kind) == category]
        rng.shuffle(group)
        result.update({key: SPLITS[index % 2] for index, key in enumerate(group)})
    return result


def generate_dataset(config: GenerationConfig = GenerationConfig()) -> SyntheticDataset:
    rng = random.Random(config.seed)
    family_splits = _family_splits(rng)
    # Registry can include accounts with no feedback. Each split gets all segments.
    per_split = max(20, min(150, config.rows // 10))
    customer_ids = [f"C{index:05d}" for index in range(1, 2 * per_split + 1)]
    rng.shuffle(customer_ids)
    customers, pools = [], {}
    for split_index, split in enumerate(SPLITS):
        pools[split] = {segment: [] for segment in SEGMENTS}
        for index in range(per_split):
            segment = SEGMENTS[index % 3]
            low, high = ARR_RANGES[segment]
            account = {
                "customer_id": customer_ids[split_index * per_split + index],
                "segment": segment, "account_value": rng.randrange(low, high + 1, 12),
                "split": split,
            }
            customers.append(account)
            pools[split][segment].append(account)

    counts = _allocate(config.rows, {"clear": 85, "overlapping": 10, "ambiguous": 5})
    theme_counts = _allocate(counts["clear"], THEME_WEIGHTS)
    records = []
    family_position = {f.key: index % 4 for index, f in enumerate(FAMILIES)}

    def record(family: Family, ordinal: int):
        split = family_splits[family.key]
        theme = family.themes[0] if family.kind == "clear" else None
        if theme == "dashboard_customisation":
            # A few vocal low-value accounts inflate record/vote volume.
            account = rng.choice(pools[split]["Startup"][:3])
        elif theme in {"audit_history", "identity_access"}:
            account = rng.choice(pools[split]["Enterprise"])
        else:
            segment = rng.choices(SEGMENTS, weights=(3, 5, 2), k=1)[0]
            account = rng.choice(pools[split][segment])
        if theme == "usage_alerts":
            # Four of every five rows per family fall in the last 30 days.
            days_ago = rng.randrange(0, 30) if ordinal % 5 else rng.randrange(30, 120)
        else:
            days_ago = rng.randrange(120)
        text = family.phrases[ordinal % len(family.phrases)]
        # Deliberate repetitions and lightweight noise, without inventing new intent.
        if ordinal % 7 == 5:
            text = text.lower()
        if ordinal % 11 == 7:
            text = "pls help: " + text
        if theme == "dashboard_customisation":
            urgency, alignment, votes = rng.randint(1, 2), rng.randint(1, 2), rng.randint(3, 9)
        elif theme in {"audit_history", "identity_access"}:
            urgency, alignment, votes = rng.randint(4, 5), 5, rng.randint(1, 2)
        else:
            urgency, alignment, votes = rng.randint(2, 5), rng.randint(2, 4), rng.randint(1, 3)
        if family.kind == "clear":
            effort = EFFORT[theme] + family_position[family.key]
        else:
            # Unclear/multiple requests have no defensible single effort estimate.
            effort = None
        if family.kind == "ambiguous":
            urgency = alignment = None
        feedback = {
            "customer_id": account["customer_id"], "feedback_text": text,
            "segment": account["segment"], "request_date": (END_DATE - timedelta(days=days_ago)).isoformat(),
            "account_value": account["account_value"], "votes": votes,
            "urgency": urgency, "strategic_alignment": alignment, "effort": effort,
        }
        label = {
            "split": split, "template_family": family.key, "label_kind": family.kind,
            "theme_labels": "|".join(sorted(family.themes)),
            "primary_theme": theme or "",
            "duplicate_group": family.key if family.kind == "clear" else "",
            "eligible_single_theme": family.kind == "clear",
            "eligible_duplicate": family.kind == "clear",
        }
        records.append((feedback, label))

    for category, count in {**theme_counts, "overlapping": counts["overlapping"],
                            "ambiguous": counts["ambiguous"]}.items():
        families = [f for f in FAMILIES
                    if (f.themes[0] if f.kind == "clear" else f.kind) == category]
        rng.shuffle(families)
        occurrences = Counter()
        for index in range(count):
            chosen = families[index % len(families)]
            record(chosen, occurrences[chosen.key])
            occurrences[chosen.key] += 1
    rng.shuffle(records)
    feedback_rows, label_rows = [], []
    for index, (feedback, label) in enumerate(records, start=1):
        identifier = f"F{index:06d}"
        feedback_rows.append({"feedback_id": identifier, **feedback})
        label_rows.append({"feedback_id": identifier, **label})
    feedback = pd.DataFrame(feedback_rows, columns=REQUIRED + OPTIONAL)
    for column in ("urgency", "strategic_alignment", "effort"):
        feedback[column] = feedback[column].astype("Int64")
    dataset = SyntheticDataset(config, feedback, pd.DataFrame(label_rows),
                               pd.DataFrame(customers).sort_values("customer_id").reset_index(drop=True))
    assert_integrity(dataset)
    return dataset


def assert_integrity(dataset: SyntheticDataset) -> None:
    """Fail generation before writing if core contracts or split isolation break."""
    feedback, labels, customers = dataset.feedback, dataset.labels, dataset.customers
    validation = validate_feedback(feedback)
    if not validation.valid:
        raise ValueError("Generated feedback is invalid: " + "; ".join(validation.errors))
    if len(feedback) != dataset.config.rows or len(labels) != len(feedback):
        raise ValueError("Feedback/label row count mismatch.")
    if not labels.feedback_id.is_unique or set(feedback.feedback_id) != set(labels.feedback_id):
        raise ValueError("Labels must join one-to-one to feedback IDs.")
    if set(feedback.columns) != set(REQUIRED + OPTIONAL):
        raise ValueError("Feedback must contain only the approved input schema.")
    catalog = {family.key: family for family in FAMILIES}
    if not set(labels.template_family).issubset(catalog):
        raise ValueError("Truth labels contain an unknown request family.")
    expected = {
        "label_kind": lambda family: family.kind,
        "theme_labels": lambda family: "|".join(sorted(family.themes)),
        "primary_theme": lambda family: family.themes[0] if family.kind == "clear" else "",
        "duplicate_group": lambda family: family.key if family.kind == "clear" else "",
        "eligible_single_theme": lambda family: family.kind == "clear",
        "eligible_duplicate": lambda family: family.kind == "clear",
    }
    for column, value in expected.items():
        if not labels[column].eq(labels.template_family.map(lambda key: value(catalog[key]))).all():
            raise ValueError(f"Truth annotation {column} disagrees with the authored family.")
    if not customers.customer_id.is_unique:
        raise ValueError("Customer registry IDs must be unique.")
    joined = feedback.merge(labels, on="feedback_id", validate="one_to_one")
    accounts = joined.merge(customers, on="customer_id", suffixes=("", "_registry"),
                            how="left", validate="many_to_one")
    for column in ("segment", "account_value", "split"):
        if not accounts[column].eq(accounts[column + "_registry"]).all():
            raise ValueError("Customer signals or split disagree with registry.")
    if set(labels.split) != set(SPLITS):
        raise ValueError("Both tuning and evaluation splits must be present.")
    joined["normalised_text"] = joined.feedback_text.str.casefold().str.split().str.join(" ")
    for key in ("template_family", "customer_id", "normalised_text"):
        if joined.groupby(key).split.nunique().max() > 1:
            raise ValueError(f"{key} crosses the tuning/evaluation boundary.")
    duplicates = joined[joined.duplicate_group != ""]
    if duplicates.groupby("duplicate_group").split.nunique().max() > 1:
        raise ValueError("Semantic duplicate group crosses the split boundary.")
    for split in SPLITS:
        clear = joined[(joined.split == split) & joined.eligible_single_theme]
        if set(clear.primary_theme) != set(THEME_WEIGHTS):
            raise ValueError("Every clear theme must be represented in each split.")


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, lineterminator="\n").encode("utf-8")


def dataset_summary(dataset: SyntheticDataset) -> dict:
    joined = dataset.feedback.merge(dataset.labels, on="feedback_id", validate="one_to_one")
    summary = {}
    for split in SPLITS:
        subset = joined[joined.split == split]
        summary[split] = {
            "rows": len(subset), "distinct_customers": int(subset.customer_id.nunique()),
            "unique_texts": int(subset.feedback_text.nunique()),
            "label_kinds": subset.label_kind.value_counts().sort_index().to_dict(),
            "clear_themes": subset.loc[subset.eligible_single_theme, "primary_theme"].value_counts().sort_index().to_dict(),
        }
    return summary


def write_dataset(dataset: SyntheticDataset, destination: Path) -> dict:
    """Write a new, non-overwriting bundle with deterministic bytes and hashes."""
    assert_integrity(dataset)
    payloads = {
        "inputs/feedback.csv": _csv_bytes(dataset.feedback),
        "truth/labels.csv": _csv_bytes(dataset.labels),
        "truth/customers.csv": _csv_bytes(dataset.customers),
    }
    for split in SPLITS:
        payloads[f"inputs/{split}.csv"] = _csv_bytes(dataset.feedback_for(split))
        payloads[f"model_inputs/{split}.csv"] = _csv_bytes(dataset.model_input(split))
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in sorted(payloads.items())}
    source_dir = Path(__file__).parent
    manifest = {
        "dataset_version": DATASET_VERSION, "synthetic": True,
        "seed": dataset.config.seed, "rows": dataset.config.rows,
        "date_window": {"start": START_DATE.isoformat(), "end": END_DATE.isoformat()},
        "units": {"account_value": "synthetic annual recurring revenue, USD per account",
                  "effort": "estimated person-days per request intent; do not sum repeated requests",
                  "votes": "simulated endorsements per record; not unique customers",
                  "urgency": "ordinal 1 (low) to 5 (high)",
                  "strategic_alignment": "ordinal 1–5 under a fixed illustrative enterprise/retention strategy"},
        "split_policy": "Seeded 2-of-4 whole request families per category per split; disjoint customers; approximately 50/50 rows. No random row split.",
        "model_features": ["feedback_text"], "join_key_only": "feedback_id",
        "label_policy": "Clear single-theme and specific-request duplicate labels only; overlapping/vague rows excluded from these metrics and retained for separate challenge analysis.",
        "summary": dataset_summary(dataset),
        "configuration": {"category_percent": {"clear": 85, "overlapping": 10, "ambiguous": 5},
                          "clear_theme_weights": THEME_WEIGHTS},
        "runtime": {"python": platform.python_version(), "pandas": pd.__version__},
        "source_sha256": {name: hashlib.sha256((source_dir / name).read_bytes()).hexdigest()
                          for name in ("synthetic.py", "synthetic_catalog.py", "ingestion.py")},
        "files_sha256": hashes,
        "content_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
        "limitations": [
            "Authored synthetic templates and labels, not independently annotated real feedback.",
            "Shared vocabulary and generator design remain across held-out request families.",
            "Exact repetitions within splits can inflate row-based metrics; report unique-text/family-weighted diagnostics too.",
            "Increasing record count repeats a finite catalog; it does not add independent semantic diversity.",
            "Business conflicts and emerging usage demand are deliberately constructed, not observed findings.",
            "Inspecting evaluation labels/output to tune a model compromises the holdout; freeze settings using tuning only.",
        ],
    }
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in payloads.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate explicitly synthetic ProductLens feedback and separate truth labels.")
    parser.add_argument("--rows", type=int, default=500, help="200–10,000; proposal target: 1,000–1,500")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are never overwritten")
    args = parser.parse_args(argv)
    try:
        config = GenerationConfig(rows=args.rows, seed=args.seed)
        destination = args.output or Path(f"data/generated/v{DATASET_VERSION}_seed{config.seed}_n{config.rows}")
        manifest = write_dataset(generate_dataset(config), destination)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Generation failed: {exc}\n")
    print(json.dumps({"output": str(destination.resolve()), "rows": config.rows,
                      "content_sha256": manifest["content_sha256"], "summary": manifest["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
