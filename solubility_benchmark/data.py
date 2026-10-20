"""Load measured aqueous solubility and compute an explicit descriptor set."""
from dataclasses import dataclass
import csv
import math
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

TARGET='measured log solubility in mols per litre'
FEATURE_NAMES=('molecular_weight','calculated_logp','polar_surface_area','hydrogen_bond_donors','hydrogen_bond_acceptors','rotatable_bonds','ring_count','fraction_csp3','aromatic_heavy_atom_fraction')

@dataclass
class Dataset:
    X: np.ndarray
    y: np.ndarray
    canonical: list[str]
    scaffolds: list[str]
    molecules: list


def describe(smiles):
    if not isinstance(smiles,str) or not smiles.strip():
        raise ValueError('SMILES must be a nonblank string')
    mol=Chem.MolFromSmiles(smiles)
    if mol is None or mol.GetNumHeavyAtoms()==0:
        raise ValueError('SMILES must parse to a molecule with heavy atoms')
    values=[Descriptors.MolWt(mol),Descriptors.MolLogP(mol),rdMolDescriptors.CalcTPSA(mol),
            rdMolDescriptors.CalcNumHBD(mol),rdMolDescriptors.CalcNumHBA(mol),
            rdMolDescriptors.CalcNumRotatableBonds(mol),rdMolDescriptors.CalcNumRings(mol),
            rdMolDescriptors.CalcFractionCSP3(mol),
            sum(atom.GetIsAromatic() for atom in mol.GetAtoms())/mol.GetNumHeavyAtoms()]
    if not all(math.isfinite(v) for v in values):
        raise ValueError('nonfinite descriptor')
    canonical=Chem.MolToSmiles(mol,isomericSmiles=True)
    scaffold=MurckoScaffold.MurckoScaffoldSmiles(mol=mol,includeChirality=False) or '<ACYCLIC>'
    return mol,canonical,scaffold,values


def load_dataset(path:Path)->Dataset:
    molecules=[];canonical=[];scaffolds=[];features=[];targets=[]
    with Path(path).open(newline='',encoding='utf-8') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames is None or 'smiles' not in reader.fieldnames or TARGET not in reader.fieldnames:
            raise ValueError('CSV requires smiles and measured log solubility columns')
        if len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError('duplicate CSV columns')
        for line,row in enumerate(reader,2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'row {line}: malformed CSV width')
            try:
                target=float(row[TARGET])
                if not math.isfinite(target): raise ValueError('nonfinite target')
                mol,key,scaffold,x=describe(row['smiles'])
            except (TypeError,ValueError) as e:
                raise ValueError(f'row {line}: {e}') from e
            molecules.append(mol);canonical.append(key);scaffolds.append(scaffold);features.append(x);targets.append(target)
    if len(targets)<2:
        raise ValueError('at least two records required')
    return Dataset(np.array(features,dtype=float),np.array(targets,dtype=float),canonical,scaffolds,molecules)
