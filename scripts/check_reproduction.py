"""Rerun the complete benchmark and compare numerical summaries."""
import json
from pathlib import Path
import sys
import tempfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from solubility_benchmark.analysis import study

def main():
    expected=json.loads((ROOT/'results/analysis.json').read_text())
    expected_split=json.loads((ROOT/'results/split_manifest.json').read_text())
    with tempfile.TemporaryDirectory() as temporary:
        actual=study(ROOT/'data/delaney_subset.csv',Path(temporary))
        actual_split=json.loads((Path(temporary)/'split_manifest.json').read_text())
        if actual_split!=expected_split:raise SystemExit('Split/provenance mismatch')
        for a,b in zip(actual['metrics'],expected['metrics'],strict=True):
            for key in ['split','model','train_rows','test_rows']:
                if a[key]!=b[key]:raise SystemExit(f'Metric identity mismatch: {key}')
            for key in ['rmse_log10_mol_l','mae_log10_mol_l','r2']:
                np.testing.assert_allclose(a[key],b[key],rtol=1e-9,atol=1e-10)
        if actual['selected_hyperparameters']!=expected['selected_hyperparameters']:raise SystemExit('Model-selection mismatch')
    print('Reproduced six model/partition metric rows, selected parameters, and split fingerprints.')

if __name__=='__main__':main()
