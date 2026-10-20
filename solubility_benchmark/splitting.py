"""Label-independent partitions that preserve duplicate identities."""
from collections import defaultdict
import hashlib
import numpy as np
from sklearn.model_selection import GroupShuffleSplit,GroupKFold

SEED=2026


def digest_indices(indices):
    return hashlib.sha256(','.join(map(str,sorted(map(int,indices)))).encode()).hexdigest()


def make_split(dataset,method,test_fraction=0.2,seed=SEED):
    if not 0<test_fraction<1: raise ValueError('test_fraction must be between zero and one')
    n=len(dataset.y)
    if method=='random':
        # Random assignment is by canonical structure, not individual records.
        train,test=next(GroupShuffleSplit(n_splits=1,test_size=test_fraction,random_state=seed).split(np.zeros(n),groups=dataset.canonical))
    elif method=='scaffold':
        groups=defaultdict(list)
        for i,key in enumerate(dataset.scaffolds):groups[key].append(i)
        ordered=sorted(groups.items(),key=lambda item:(-len(item[1]),item[0]))
        cutoff=(1-test_fraction)*n;train=[];test=[]
        for _,indices in ordered:
            if len(train)+len(indices)<=cutoff:train.extend(indices)
            else:test.extend(indices)
        train=np.array(sorted(train));test=np.array(sorted(test))
    else:raise ValueError('method must be random or scaffold')
    if len(train)==0 or len(test)==0:raise ValueError('group sizes do not permit nonempty train/test partitions')
    if set(train)&set(test) or set(train)|set(test)!=set(range(n)):raise RuntimeError('invalid partition')
    if set(dataset.canonical[i] for i in train)&set(dataset.canonical[i] for i in test):raise RuntimeError('duplicate structure crossed partition')
    if method=='scaffold' and set(dataset.scaffolds[i] for i in train)&set(dataset.scaffolds[i] for i in test):raise RuntimeError('scaffold crossed partition')
    return np.asarray(train,dtype=int),np.asarray(test,dtype=int)


def training_folds(groups):
    count=len(set(groups))
    if count<2:raise ValueError('at least two training groups required')
    return list(GroupKFold(n_splits=min(5,count)).split(np.zeros(len(groups)),groups=groups))
