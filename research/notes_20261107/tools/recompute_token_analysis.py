"""Recompute the existing four-row comparison; no API or simulator calls."""
from pathlib import Path
import csv,json,math,sys
source=Path(sys.argv[1]);destination=Path(sys.argv[2])
with source.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
assert len(rows)==4
out=[]
for row in rows:
    a_in,a_cache,a_out,a_total=(float(row[k]) for k in ['A_mean_input','A_mean_cached_input','A_mean_output','A_mean_total'])
    b_in,b_cache,b_out,b_total=(float(row[k]) for k in ['B_mean_input','B_mean_cached_input','B_mean_output','B_mean_total'])
    assert 0<=a_cache<=a_in and 0<=b_cache<=b_in
    assert math.isclose(a_in+a_out,a_total,rel_tol=1e-10)
    assert math.isclose(b_in+b_out,b_total,rel_tol=1e-10)
    total_ratio=a_total/b_total
    uncached_ratio=(a_in-a_cache+a_out)/(b_in-b_cache+b_out)
    assert math.isclose(total_ratio,float(row['A_div_B_total']),rel_tol=1e-10)
    assert math.isclose(uncached_ratio,float(row['A_div_B_uncached_metric']),rel_tol=1e-10)
    out.append({'task':row['task'],'A_method':row['A_method'],'A_n':int(row['A_episodes']),'B_n':int(row['B_episodes']),'A_successes':int(row['A_successes']),'B_successes':int(row['B_successes']),'A_mean_total':a_total,'B_mean_total':b_total,'total_ratio':total_ratio,'uncached_metric_ratio':uncached_ratio,'A_cached_fraction_of_input':a_cache/a_in,'B_cached_fraction_of_input':b_cache/b_in,'B_actual_HTTP_mean':float(row['B_mean_actual_HTTP']),'A_actual_HTTP_count':row['A_HTTP_count']})
summary={'analysis_type':'Recalculation of existing historical table; no new experiments.','rows':out,'total_ratio_range':[min(x['total_ratio'] for x in out),max(x['total_ratio'] for x in out)],'uncached_metric_ratio_range':[min(x['uncached_metric_ratio'] for x in out),max(x['uncached_metric_ratio'] for x in out)],'A_cached_input_fraction_range':[min(x['A_cached_fraction_of_input'] for x in out),max(x['A_cached_fraction_of_input'] for x in out)],'qualifications':['Different models, tokenizers, layouts and success rates.','B task groups are reused across A modes, not four independent B cohorts.','Uncached metric is a descriptive accounting view, not a price or causal estimator.','Project A actual HTTP count is not established by action-segment counts.']}
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['total_ratio_range','uncached_metric_ratio_range','A_cached_input_fraction_range']},ensure_ascii=False))
