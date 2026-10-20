"""A small solubility benchmark; no molecule design or clinical predictions."""
import argparse
from collections import Counter
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
from rdkit import DataStructs
from rdkit.Chem import rdFingerprintGenerator
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import FEATURE_NAMES,load_dataset
from .splitting import SEED,digest_indices,make_split,training_folds
ROOT=Path(__file__).resolve().parents[1]


def display_metric(value, digits=3):
    """Render an undefined statistic without disguising it as a numeric score."""
    return 'undefined' if value is None else f'{value:.{digits}f}'


def regression_metrics(y,p):
    y=np.asarray(y,dtype=float);p=np.asarray(p,dtype=float)
    if y.ndim!=1 or p.shape!=y.shape or len(y)<2 or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError('metrics need finite equal one-dimensional arrays with at least two records')
    return {'rmse_log10_mol_l':float(np.sqrt(mean_squared_error(y,p))),
            'mae_log10_mol_l':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)) if np.var(y)>0 else None}


def distance_diagnostics(X_train,X_test):
    """Fit scaling and reference thresholds on training descriptors only."""
    if len(X_train)<2:raise ValueError('two training records required')
    scaler=StandardScaler().fit(X_train)
    train=scaler.transform(X_train);test=scaler.transform(X_test)
    nn=NearestNeighbors(n_neighbors=2).fit(train)
    reference=nn.kneighbors(train,return_distance=True)[0][:,1]
    distances=nn.kneighbors(test,n_neighbors=1,return_distance=True)[0][:,0]
    q50,q90=map(float,np.quantile(reference,[0.5,0.9]))
    labels=np.where(distances<=q50,'at_or_below_training_q50',np.where(distances<=q90,'training_q50_to_q90','above_training_q90'))
    return distances,labels,{'training_loo_distance_q50':q50,'training_loo_distance_q90':q90,'distance':'Euclidean after training-only standardization; descriptive, not a validated applicability-domain boundary'}


def model_specs():
    return {
        'ridge':(Pipeline([('scale',StandardScaler()),('model',Ridge())]),{'model__alpha':[0.1,1.0,10.0,100.0]}),
        'random_forest':(Pipeline([('model',RandomForestRegressor(n_estimators=150,random_state=SEED,n_jobs=1))]),
                         {'model__min_samples_leaf':[1,3],'model__max_features':[0.7,1.0]})}


def tune(X,y,groups,name):
    estimator,params=model_specs()[name]
    folds=training_folds(groups)
    search=GridSearchCV(estimator,params,cv=folds,scoring='neg_root_mean_squared_error',refit=True,n_jobs=1,error_score='raise').fit(X,y)
    rows=[{'model':name,'parameters':json.dumps(p,sort_keys=True),'mean_inner_rmse':float(-mean),'std_inner_rmse':float(std)} for p,mean,std in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'],search.cv_results_['std_test_score'])]
    return search.best_estimator_,search.best_params_,rows


def save_csv(path,rows):
    if not rows:raise ValueError('empty output table')
    with Path(path).open('w',newline='',encoding='utf-8') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def study(path,output):
    trusted=ROOT/'data/delaney_subset.csv'
    if Path(path).resolve()==trusted.resolve():
        manifest_data=json.loads((ROOT/'data/manifest.json').read_text())
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=manifest_data['subset_sha256']:
            raise ValueError('Pinned input SHA-256 mismatch; do not silently change the benchmark')
    dataset=load_dataset(path)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    splits={method:make_split(dataset,method) for method in ['random','scaffold']}
    manifest={'seed':SEED,'input_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'rows':len(dataset.y),
              'features':list(FEATURE_NAMES),'source_predictor_used':False,'split_label_usage':'none',
              'duplicate_structure_extra_rows':len(dataset.y)-len(set(dataset.canonical)),
              'unique_scaffolds':len(set(dataset.scaffolds)),'acyclic_rows':dataset.scaffolds.count('<ACYCLIC>'),
              'splits':{method:{'train_rows':len(train),'test_rows':len(test),'train_indices_sha256':digest_indices(train),'test_indices_sha256':digest_indices(test),
              'train_groups':len(set((dataset.canonical if method=='random' else dataset.scaffolds)[i] for i in train)),
              'test_scaffold_overlap_fraction':sum(dataset.scaffolds[i] in {dataset.scaffolds[j] for j in train} for i in test)/len(test)} for method,(train,test) in splits.items()}}
    # Freeze split identities before any fit or test score computation.
    (output/'split_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    metrics=[];cv_rows=[];distance_rows=[];similarity_rows=[];predictions={};distance_parameters={};selected_parameters={}
    fingerprint=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
    fps=[fingerprint.GetFingerprint(mol) for mol in dataset.molecules]
    for method,(train,test) in splits.items():
        X_train,y_train=dataset.X[train],dataset.y[train]
        X_test,y_test=dataset.X[test],dataset.y[test]
        groups=[(dataset.canonical if method=='random' else dataset.scaffolds)[i] for i in train]
        distances,bins,params=distance_diagnostics(X_train,X_test);distance_parameters[method]=params
        nearest=[max(DataStructs.BulkTanimotoSimilarity(fps[i],[fps[j] for j in train])) for i in test]
        similarity_rows.append({'split':method,'test_rows':len(test),'mean_nearest_training_tanimoto':float(np.mean(nearest)),
                                'median_nearest_training_tanimoto':float(np.median(nearest)),'maximum_nearest_training_tanimoto':max(nearest),
                                'fraction_at_least_0_8':float(np.mean(np.asarray(nearest)>=0.8))})
        selected_parameters[method]={}
        models={'training_mean':DummyRegressor(strategy='mean').fit(X_train,y_train)}
        for name in model_specs():
            fit,parameters,candidates=tune(X_train,y_train,groups,name)
            models[name]=fit;selected_parameters[method][name]=parameters
            for row in candidates:
                row['split']=method;row['selected']=json.loads(row['parameters'])==parameters;cv_rows.append(row)
        predictions[method]={}
        for name,model in models.items():
            pred=model.predict(X_test)
            predictions[method][name]=(y_test,pred)
            metrics.append({'split':method,'model':name,'train_rows':len(train),'test_rows':len(test),**regression_metrics(y_test,pred)})
            for label in ['at_or_below_training_q50','training_q50_to_q90','above_training_q90']:
                mask=bins==label;n=int(mask.sum())
                distance_rows.append({'split':method,'model':name,'distance_bin':label,'test_rows':n,
                                     'mean_nearest_training_distance':float(np.mean(distances[mask])) if n else None,
                                     'mae_log10_mol_l':float(mean_absolute_error(y_test[mask],pred[mask])) if n else None,
                                     'rmse_log10_mol_l':float(np.sqrt(mean_squared_error(y_test[mask],pred[mask]))) if n else None})
    save_csv(output/'metrics.csv',metrics);save_csv(output/'training_cv.csv',cv_rows);save_csv(output/'distance_error_bins.csv',distance_rows);save_csv(output/'structural_similarity.csv',similarity_rows)
    payload={'status':'educational retrospective solubility benchmark; no external or prospective validation',
             'versions':{p:importlib.metadata.version(p) for p in ['numpy','scikit-learn','scipy','matplotlib','rdkit']},
             'metrics':metrics,'selected_hyperparameters':selected_parameters,'training_distance_parameters':distance_parameters,'structural_similarity':similarity_rows,
             'preprocessing':'Descriptors recomputed from each provided SMILES; no salt/tautomer normalization; duplicate identities stay together',
             'uncertainty':'Single fixed partition per strategy; no confidence or transportability guarantee. Comparisons change both composition and structural overlap.'}
    (output/'analysis.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    draw(predictions,metrics,distance_rows,output)
    report=['# Measured aqueous-solubility benchmark','',
            'Target: log10 of measured solubility in mol/L. Lower error is better. These are retrospective results for two different fixed test partitions, not a causal estimate of the effect of scaffold overlap.','',
            '| Partition | Model | Test records | RMSE (log10 mol/L) | MAE (log10 mol/L) | R² |','| --- | --- | ---: | ---: | ---: | ---: |']
    report += [f"| {r['split']} | {r['model']} | {r['test_rows']} | {r['rmse_log10_mol_l']:.3f} | {r['mae_log10_mol_l']:.3f} | {display_metric(r['r2'])} |" for r in metrics]
    report += ['', '![Model errors](model_errors.png)','', '![Observed and predicted solubility](predictions.png)','',
               '## Distance is a diagnostic, not a certificate','',
               'Nearest-training distances use nine standardized descriptors. Scaling and distance-bin cutoffs use training data only. Wider-distance bins can reveal error patterns, but they are not calibrated uncertainty intervals or validated applicability-domain limits. Small bins are unstable; counts are shown.','',
               '![Distance-bin errors](distance_error_bins.png)','',
               'Different scaffold labels do not ensure low chemical similarity. See [structural similarity](structural_similarity.csv) for nearest-training Morgan-fingerprint similarities, and [methods](../docs/methods.md) for the acyclic-group rule and selection limits.','',
               'No molecule is proposed, optimized, ranked for therapeutic use, or given a safety/efficacy recommendation.','']
    (output/'report.md').write_text('\n'.join(report))
    return payload


def draw(predictions,metrics,distance_rows,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120})
    colors={'training_mean':'#777777','ridge':'#0072B2','random_forest':'#D55E00'}
    fig,ax=plt.subplots(figsize=(8,4.6),layout='constrained')
    labels=[];values=[];cs=[]
    for row in metrics:labels.append(row['split']+'\n'+row['model'].replace('_',' '));values.append(row['rmse_log10_mol_l']);cs.append(colors[row['model']])
    ax.bar(np.arange(len(values)),values,color=cs);ax.set_xticks(np.arange(len(values)),labels,rotation=22,ha='right');ax.set_ylabel('Test RMSE (log10 mol/L)');ax.set_title('One fixed partition per strategy · lower is better')
    fig.savefig(output/'model_errors.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4.8),layout='constrained')
    for ax,method in zip(axes,['random','scaffold']):
        actual,pred=predictions[method]['random_forest'];low=min(actual.min(),pred.min());high=max(actual.max(),pred.max())
        ax.scatter(actual,pred,s=12,alpha=.55,color=colors['random_forest']);ax.plot([low,high],[low,high],'--',color='#666666');ax.set(title=method+' · random forest',xlabel='Observed log10 solubility (mol/L)',ylabel='Predicted log10 solubility (mol/L)')
    fig.suptitle('Held-out observations; model chosen for display before evaluation')
    fig.savefig(output/'predictions.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4.8),layout='constrained')
    labels=['≤ training q50','q50 to q90','> training q90']
    for ax,method in zip(axes,['random','scaffold']):
        rows=[r for r in distance_rows if r['model']=='random_forest' and r['split']==method]
        vals=[r['mae_log10_mol_l'] if r['mae_log10_mol_l'] is not None else 0 for r in rows]
        ax.bar(range(3),vals,color=colors['random_forest']);ax.set_xticks(range(3),labels,rotation=15);ax.set(title=method+' · random forest',ylabel='Test MAE (log10 mol/L)')
        for i,(v,r) in enumerate(zip(vals,rows)):ax.text(i,v+.03,'n='+str(r['test_rows']),ha='center')
        ax.set_ylim(0,max(vals+[.2])*1.25)
    fig.suptitle('Descriptor distance groups · descriptive error summaries')
    fig.savefig(output/'distance_error_bins.png',dpi=150);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=ROOT/'data/delaney_subset.csv')
    parser.add_argument('--output',type=Path,default=ROOT/'results')
    args=parser.parse_args()
    result=study(args.data,args.output)
    print(json.dumps(result['metrics'],indent=2))

if __name__=='__main__':main()
