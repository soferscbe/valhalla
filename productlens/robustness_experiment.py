"""Predeclared synthetic business-signal robustness diagnostics; no truth labels."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from productlens.grouping import GroupingConfig, group_feedback
from productlens.ingestion import read_feedback, validate_feedback
from productlens.ranking_experiment import ROOT, digest
from productlens.scoring import METHODS, aggregate_evidence, compare_scores, score_opportunities
from productlens.embeddings import MODEL_ID, MODEL_REVISION


def perturbations(data, assignments):
    """Stable ID order makes seeded transformations independent of incoming row order."""
    data = data.sort_values('feedback_id').reset_index(drop=True)
    customers = sorted(data.customer_id.unique())
    yield 'permuted', data.sample(frac=1, random_state=20261111), True, {}
    chosen = customers[0]
    rows = data[data.customer_id == chosen]
    copies = [rows.assign(feedback_id=rows.feedback_id.map(lambda v: f'REPEAT-{i}-{v}')) for i in range(10)]
    repeated = pd.concat([data, *copies], ignore_index=True)
    if len(repeated) > 2000 or repeated.feedback_id.duplicated().any():
        raise ValueError('Repetition scenario exceeds row cap or collides with input IDs.')
    yield 'repeated_account', repeated, True, {'customer_id': chosen, 'added_rows': len(repeated)-len(data)}
    factors = dict(zip(customers, np.random.default_rng(20261111).uniform(.8, 1.2, len(customers))))
    changed = data.copy()
    changed.account_value *= changed.customer_id.map(factors)
    yield 'arr_uncertainty', changed, False, {'customer_multipliers': factors}
    ids = sorted(assignments.duplicate_group_id.unique())
    factors = dict(zip(ids, np.random.default_rng(20261112).uniform(.8, 1.2, len(ids))))
    lookup = assignments.set_index('feedback_id').duplicate_group_id.map(factors)
    changed = data.copy()
    changed.effort *= changed.feedback_id.map(lookup)
    yield 'effort_uncertainty', changed, False, {'subgroup_multipliers': factors}
    selected = sorted(np.random.default_rng(20261113).choice(customers, size=int(np.ceil(len(customers)*.1)), replace=False).tolist())
    changed = data.copy()
    changed.loc[changed.customer_id.isin(selected), 'account_value'] = np.nan
    yield 'arr_missing', changed, False, {'masked_customers': selected}


def top_ids(scores):
    return scores.dropna(subset=['priority_score']).sort_values(['priority_score','opportunity_id'], ascending=[False, True]).head(5).opportunity_id.tolist()


def compare(base, changed):
    combined = base[['opportunity_id','priority_score']].merge(changed[['opportunity_id','priority_score']].rename(columns={'priority_score':'changed'}), on='opportunity_id', how='outer', validate='one_to_one')
    original = top_ids(base)
    return {'common_candidate_comparison': compare_scores(combined,'priority_score','changed'),
            'base_top5': original, 'scenario_top5': top_ids(changed),
            'base_top5_retention': len(set(original)&set(top_ids(changed)))/len(original) if original else None,
            'became_unranked': int((combined.priority_score.notna() & combined.changed.isna()).sum())}


def run(input_path, config_path, output, reference=None):
    input_path, config_path, output = map(Path, (input_path, config_path, output))
    if output.exists():
        raise ValueError('Output directory already exists; preserve experiment evidence.')
    config = json.loads(config_path.read_text())
    if (config['model_id'], config['model_revision']) != (MODEL_ID, MODEL_REVISION):
        raise ValueError('Frozen model mismatch.')
    checked = validate_feedback(read_feedback(input_path.read_bytes(), input_path.name))
    if not checked.valid:
        raise ValueError('; '.join(checked.errors))
    data = checked.data
    groups = group_feedback(data, GroupingConfig(**config['grouping']))
    base = score_opportunities(aggregate_evidence(data, groups.assignments)).scores
    if reference:
        ref = Path(reference)
        cols = ['feedback_id','opportunity_id','duplicate_group_id']
        pd.testing.assert_frame_equal(groups.assignments[cols].sort_values('feedback_id').reset_index(drop=True), pd.read_csv(ref/'assignments.csv')[cols].sort_values('feedback_id').reset_index(drop=True), check_dtype=False)
        pd.testing.assert_frame_equal(base.set_index('opportunity_id')[list(METHODS)].sort_index(), pd.read_csv(ref/'scores_balanced.csv').set_index('opportunity_id')[list(METHODS)].sort_index(), check_exact=False, atol=1e-10, rtol=0)
    output.mkdir(parents=True)
    report = {'protocol':'data-robustness-v1','input_sha256':digest(input_path), 'config_sha256':digest(config_path),
              'source_sha256':{p:digest(ROOT/p) for p in ['productlens/robustness_experiment.py','productlens/grouping.py','productlens/scoring.py','docs/ROBUSTNESS_PROTOCOL.md']},
              'reference_reproduction_verified':bool(reference),'base_rows':len(data),'base_candidates':len(base),
              'base_coverage':int(base.priority_score.notna().sum()),'scenarios':{}}
    base.to_csv(output/'base_scores.csv',index=False)
    for name, changed, regroup, details in perturbations(data, groups.assignments):
        destination = output/name
        destination.mkdir()
        assignments = group_feedback(changed, GroupingConfig(**config['grouping'])).assignments if regroup else groups.assignments
        scores = score_opportunities(aggregate_evidence(changed, assignments)).scores
        changed.to_csv(destination/'input.csv',index=False)
        assignments.to_csv(destination/'assignments.csv',index=False)
        scores.to_csv(destination/'scores.csv',index=False)
        result = {'rows':len(changed),'candidates':len(scores),'scored':int(scores.priority_score.notna().sum()),
                  'input_sha256':digest(destination/'input.csv'),'changes':details,**compare(base,scores)}
        assert set(assignments.feedback_id)==set(changed.feedback_id) and len(assignments)==len(changed)
        result['traceability']=1.0
        if name in ('permuted','repeated_account'):
            fields=['distinct_customers','arr','urgency','alignment','effort_proxy','priority_score','rice_score','weighted_score']
            pd.testing.assert_frame_equal(base.set_index('opportunity_id')[fields].sort_index(),scores.set_index('opportunity_id')[fields].sort_index(),check_exact=False,atol=1e-10,rtol=0)
            original=assignments[assignments.feedback_id.isin(data.feedback_id)]
            pd.testing.assert_frame_equal(groups.assignments.sort_values('feedback_id').reset_index(drop=True),original.sort_values('feedback_id').reset_index(drop=True),check_exact=False,atol=1e-10,rtol=0)
            result['invariance_verified']=True
        report['scenarios'][name]=result
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=ROOT/'config/semantic.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path)
    args=parser.parse_args()
    report=run(args.input,args.config,args.output,args.reference)
    print(json.dumps({n:{k:v for k,v in r.items() if k not in ('changes','common_candidate_comparison')} for n,r in report['scenarios'].items()},indent=2))

if __name__=='__main__':
    main()
