"""Recreate the attributed two-column subset from pinned public sources."""
from collections import defaultdict
import csv
import hashlib
from io import StringIO
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/manifest.json').read_text())

def fetch(url,expected):
    with urllib.request.urlopen(url,timeout=60) as response:raw=response.read(2_000_001)
    if len(raw)>2_000_000 or hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('Source changed: do not substitute a different benchmark silently')
    return raw

def main():
    processed=fetch(manifest['deepchem_url'],manifest['deepchem_sha256'])
    original=fetch(manifest['original_download_url'],manifest['original_sha256'])
    candidates=defaultdict(list)
    for row in csv.DictReader(StringIO(original.decode())):
        candidates[(row['SMILES'].strip(),round(float(row['measured log(solubility:mol/L)']),6))].append(row['measured log(solubility:mol/L)'])
    selected=[]
    for row in csv.DictReader(StringIO(processed.decode())):
        smiles=row['smiles'].strip();key=(smiles,round(float(row['measured log solubility in mols per litre']),6))
        if not candidates[key]:raise ValueError('Unmatched original record')
        selected.append({'smiles':smiles,'measured log solubility in mols per litre':candidates[key].pop(0)})
    output=StringIO(newline='');writer=csv.DictWriter(output,fieldnames=['smiles','measured log solubility in mols per litre']);writer.writeheader();writer.writerows(selected)
    result=output.getvalue().encode()
    if hashlib.sha256(result).hexdigest()!=manifest['subset_sha256']:raise ValueError('Rebuilt subset hash mismatch')
    target=ROOT/'data/delaney_subset.csv';target.write_bytes(result)
    print(f'Rebuilt {len(selected)} attributed records; SHA-256 verified.')

if __name__=='__main__':main()
