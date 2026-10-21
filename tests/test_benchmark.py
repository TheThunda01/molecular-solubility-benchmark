import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from solubility_benchmark.data import Dataset,FEATURE_NAMES,TARGET,describe,load_dataset
from solubility_benchmark.splitting import digest_indices,make_split,training_folds
from solubility_benchmark.analysis import distance_diagnostics,regression_metrics,tune,study


def sample_dataset():
    smiles=['CCO','OCC','CCC','CCCO','c1ccccc1','Cc1ccccc1','c1ccncc1','Cc1ccncc1','C1CCCCC1','CC1CCCCC1','c1ccoc1','Cc1ccoc1','c1ccsc1','Cc1ccsc1','C1CCOC1','CC1CCOC1']
    described=[describe(s) for s in smiles]
    return Dataset(np.array([d[3] for d in described]),np.linspace(-4,1,len(smiles)),[d[1] for d in described],[d[2] for d in described],[d[0] for d in described])


class DataTests(unittest.TestCase):
    def test_pinned_dataset_integrity(self):
        root=Path(__file__).resolve().parents[1]
        manifest=json.loads((root/'data/manifest.json').read_text())
        path=root/'data/delaney_subset.csv'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),manifest['subset_sha256'])
        dataset=load_dataset(path)
        self.assertEqual(len(dataset.y),1128)
        self.assertEqual(len(set(dataset.canonical)),1117)

    def test_descriptor_shape_and_finiteness(self):
        _,_,_,values=describe('CCO')
        self.assertEqual(len(values),len(FEATURE_NAMES));self.assertTrue(np.isfinite(values).all())

    def test_equivalent_smiles_share_identity(self):
        self.assertEqual(describe('CCO')[1],describe('OCC')[1])

    def test_same_ring_substitutions_share_scaffold(self):
        self.assertEqual(describe('c1ccccc1')[2],describe('Cc1ccccc1')[2])

    def test_all_acyclic_molecules_share_declared_group(self):
        self.assertEqual(describe('CCO')[2],'<ACYCLIC>');self.assertEqual(describe('CCCC')[2],'<ACYCLIC>')

    def test_bad_smiles_fails(self):
        for value in ['', 'not-a-smiles']:
            with self.assertRaises(ValueError):describe(value)

    def test_source_prediction_cannot_enter_features(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'data.csv'
            def write(pred):
                with p.open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=['smiles',TARGET,'ESOL predicted log solubility in mols per litre']);w.writeheader();w.writerows([{'smiles':'CCO',TARGET:'0.1','ESOL predicted log solubility in mols per litre':pred},{'smiles':'CCC',TARGET:'-1','ESOL predicted log solubility in mols per litre':pred}])
            write('1');first=load_dataset(p).X;write('999999');second=load_dataset(p).X
            np.testing.assert_array_equal(first,second)

    def test_nonfinite_target_fails(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'data.csv';p.write_text('smiles,'+TARGET+'\nCCO,NaN\nCCC,2\n')
            with self.assertRaises(ValueError):load_dataset(p)


class SplitTests(unittest.TestCase):
    def test_identity_group_random_split(self):
        d=sample_dataset();train,test=make_split(d,'random')
        self.assertFalse(set(d.canonical[i] for i in train)&set(d.canonical[i] for i in test))
        self.assertEqual(set(train)|set(test),set(range(len(d.y))))

    def test_scaffold_group_split(self):
        d=sample_dataset();train,test=make_split(d,'scaffold')
        self.assertFalse(set(d.scaffolds[i] for i in train)&set(d.scaffolds[i] for i in test))

    def test_split_is_label_independent(self):
        d=sample_dataset();changed=deepcopy(d);changed.y=changed.y[::-1]*100
        for method in ['random','scaffold']:
            a=make_split(d,method);b=make_split(changed,method)
            np.testing.assert_array_equal(a[0],b[0]);np.testing.assert_array_equal(a[1],b[1])

    def test_inner_folds_are_disjoint_by_group(self):
        groups=['a','a','b','c','d','d','e','f']
        for train,test in training_folds(groups):
            self.assertFalse(set(groups[i] for i in train)&set(groups[i] for i in test))

    def test_invalid_method_and_fraction(self):
        with self.assertRaises(ValueError):make_split(sample_dataset(),'other')
        with self.assertRaises(ValueError):make_split(sample_dataset(),'random',test_fraction=1)

    def test_index_hash_is_order_independent(self):
        self.assertEqual(digest_indices([1,2,3]),digest_indices([3,1,2]))


class MetricTests(unittest.TestCase):
    def test_metrics(self):
        r=regression_metrics([0,1],[0,0])
        self.assertAlmostEqual(r['rmse_log10_mol_l'],2**-.5);self.assertEqual(r['mae_log10_mol_l'],.5);self.assertEqual(r['r2'],-1)

    def test_constant_target_r2_is_undefined(self):
        self.assertIsNone(regression_metrics([1,1],[1,2])['r2'])

    def test_metric_invalid_inputs_fail(self):
        for actual,pred in [([1],[1]),([1,2],[1]),([1,2],[float('nan'),2])]:
            with self.assertRaises(ValueError):regression_metrics(actual,pred)

    def test_distance_thresholds_ignore_test_distribution(self):
        train=np.array([[0.,0.],[1.,1.],[2.,3.],[4.,7.]])
        _,_,a=distance_diagnostics(train,np.array([[1.,2.]]))
        _,_,b=distance_diagnostics(train,np.array([[999.,999.]]))
        self.assertEqual(a,b)

    def test_near_and_distant_descriptor_points(self):
        train=np.array([[0.,0.],[1.,1.],[2.,3.],[4.,7.]])
        dist,bins,_=distance_diagnostics(train,np.array([[0.,0.],[999.,999.]]))
        # Distance kernels can leave square-rooted roundoff for identical points.
        np.testing.assert_allclose(dist[0],0,rtol=0,atol=1e-7)
        self.assertEqual(bins[1],'above_training_q90')

    def test_constant_target_complete_report_marks_r2_undefined(self):
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import Ridge
        from sklearn.ensemble import RandomForestRegressor
        dataset=sample_dataset()
        small_specs={
            'ridge':(Pipeline([('scale',StandardScaler()),('model',Ridge())]),{'model__alpha':[1.0]}),
            'random_forest':(Pipeline([('model',RandomForestRegressor(n_estimators=2,random_state=2026,n_jobs=1))]),{'model__min_samples_leaf':[1]})}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'constant.csv'
            with path.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=['smiles',TARGET]);writer.writeheader()
                writer.writerows({'smiles':smiles,TARGET:1.0} for smiles in dataset.canonical)
            output=Path(directory)/'results'
            with patch('solubility_benchmark.analysis.model_specs',return_value=small_specs):
                result=study(path,output)
            self.assertEqual(len(result['metrics']),6)
            self.assertTrue(all(row['r2'] is None for row in result['metrics']))
            report=(output/'report.md').read_text()
            self.assertEqual(report.count('undefined'),6)
            self.assertTrue((output/'predictions.png').is_file())

    def test_ridge_scaler_fits_training_only(self):
        d=sample_dataset();model,_,_=tune(d.X[:12],d.y[:12],d.canonical[:12],'ridge')
        np.testing.assert_allclose(model.named_steps['scale'].mean_,d.X[:12].mean(axis=0))

if __name__=='__main__':unittest.main()
