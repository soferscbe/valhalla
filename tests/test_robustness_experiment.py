import numpy as np
import pandas as pd
import pytest
from productlens.robustness_experiment import perturbations, compare, run
from productlens.grouping import group_feedback
from productlens.ingestion import read_feedback, validate_feedback
from pathlib import Path


def test_perturbations_preserve_customer_and_subgroup_consistency():
    data=pd.DataFrame(dict(feedback_id=['1','2','3','4'],customer_id=['a','a','b','c'],account_value=[100.,100.,200.,300.],effort=[2.,2.,3.,4.]))
    links=pd.DataFrame(dict(feedback_id=data.feedback_id,duplicate_group_id=['x','x','y','z']))
    scenarios={name:(frame,details) for name,frame,_,details in perturbations(data,links)}
    repeated=scenarios['repeated_account'][0]
    assert len(repeated)==24 and repeated.feedback_id.is_unique
    arr=scenarios['arr_uncertainty'][0]
    assert arr.groupby('customer_id').account_value.nunique().max()==1
    effort=scenarios['effort_uncertainty'][0]
    assert effort.effort.iloc[0]==effort.effort.iloc[1]
    missing,detail=scenarios['arr_missing']
    assert missing.loc[missing.customer_id.isin(detail['masked_customers']),'account_value'].isna().all()
    shuffled={n:f for n,f,_,_ in perturbations(data.sample(frac=1,random_state=9),links)}
    pd.testing.assert_frame_equal(arr,shuffled['arr_uncertainty'])


def test_coverage_loss_is_not_hidden_by_common_agreement():
    base=pd.DataFrame({'opportunity_id':list('abcdef'),'priority_score':[6.,5.,4.,3.,2.,1.]})
    changed=base.copy();changed.loc[0,'priority_score']=np.nan
    result=compare(base,changed)
    assert result['became_unranked']==1
    assert result['base_top5_retention']==.8
    assert result['common_candidate_comparison']['top_k_agreement']==1.


def test_runner_preserves_outputs_and_reproduces(tmp_path,monkeypatch):
    monkeypatch.setattr('productlens.robustness_experiment.group_feedback',lambda data,config:group_feedback(data,config,lambda texts:(np.eye(len(texts)),[False]*len(texts))))
    source=Path(__file__).resolve().parents[1]
    first=tmp_path/'first';second=tmp_path/'second'
    r=run(source/'data/sample_feedback.csv',source/'config/semantic.json',first)
    assert len(r['scenarios'])==5
    assert r['scenarios']['repeated_account']['invariance_verified']
    run(source/'data/sample_feedback.csv',source/'config/semantic.json',second)
    for p in first.rglob('*.csv'):
        assert p.read_bytes()==(second/p.relative_to(first)).read_bytes()
    with pytest.raises(ValueError,match='already exists'):
        run(source/'data/sample_feedback.csv',source/'config/semantic.json',first)
