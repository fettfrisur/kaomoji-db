"""Semantic candidate retrieval. Returns candidates, never chooses a final expression."""
import os
# Official process-lifetime opt-out; must precede any ONNX Runtime import.
os.environ["ORT_DISABLE_TELEMETRY"]="1"
os.environ["HF_HUB_DISABLE_TELEMETRY"]="1"
import argparse,json,re,sqlite3,time,hashlib
from pathlib import Path
from difflib import SequenceMatcher
ROOT=Path(__file__).resolve().parent
MODEL='sentence-transformers/all-MiniLM-L6-v2'
def catalogue():return [json.loads(s) for s in (ROOT/'catalogue.jsonl').read_text().splitlines()]
def fingerprint():return hashlib.sha256((ROOT/'catalogue.jsonl').read_bytes()).hexdigest()
def model():
 from fastembed import TextEmbedding
 return TextEmbedding(MODEL,cache_dir=os.environ.get('KAOMOJI_MODEL_CACHE',str(ROOT/'.cache'/'embeddings')),threads=2)
def index():
 import numpy as np
 rows=catalogue();texts=list(dict.fromkeys(r['search_text'] for r in rows));lookup={s:i for i,s in enumerate(texts)}
 embedder=model();vec=np.array(list(embedder.embed(texts,batch_size=64)),dtype=np.float32)
 vec/=np.maximum(np.linalg.norm(vec,axis=1,keepdims=True),1e-12)
 np.savez_compressed(ROOT/'vectors.npz',vectors=vec,mapping=np.array([lookup[r['search_text']] for r in rows]),fingerprint=fingerprint(),model=MODEL)
 print(json.dumps({'faces':len(rows),'embedded_descriptions':len(texts),'dimensions':vec.shape[1]}))
def search(query,k=12,max_length=40,curated=False,lexical=False,embedder=None):
 rows=catalogue();byid={r['id']:i for i,r in enumerate(rows)}
 if lexical:
  scores=[0.0]*len(rows);tokens=re.findall(r'\w+',query)
  if not tokens:return []
  db=sqlite3.connect(ROOT/'catalogue.sqlite')
  match=' OR '.join('"'+s+'"' for s in tokens)
  for ident,rank in db.execute('SELECT id,bm25(kaomoji_fts) FROM kaomoji_fts WHERE kaomoji_fts MATCH ? ORDER BY bm25(kaomoji_fts) LIMIT 2000',(match,)):scores[byid[ident]]=-rank
  db.close()
 else:
  import numpy as np
  p=ROOT/'vectors.npz'
  if not p.exists():raise SystemExit('Run query.py --index first, or use --lexical.')
  with np.load(p,allow_pickle=False) as data:
   if str(data['fingerprint'])!=fingerprint() or str(data['model'])!=MODEL:raise SystemExit('Catalogue/model changed; rebuild index.')
   m=embedder or model();q=np.array(next(m.embed([query])),dtype=np.float32);q/=max(np.linalg.norm(q),1e-12)
   scores=(data['vectors']@q)[data['mapping']]
 candidates=[i for i,r in enumerate(rows) if r['length']<=max_length and '\n' not in r['face'] and (not curated or r['annotation_kind']=='individual interpretation') and (not lexical or scores[i]>0)]
 # Better annotated entries win close ties, without excluding the large catalogue.
 candidates.sort(key=lambda i:float(scores[i])+(0.015 if rows[i]['annotation_kind']=='individual interpretation' else 0),reverse=True)
 selected=[];desc_counts={}
 for i in candidates:
  row=rows[i]
  if desc_counts.get(row['search_text'],0)>=2:continue
  compact=re.sub(r'\s+','',row['face'])
  if any(SequenceMatcher(None,compact,re.sub(r'\s+','',s['face'])).ratio()>.82 for s in selected):continue
  selected.append({**row,'score':round(float(scores[i]),4)});desc_counts[row['search_text']]=desc_counts.get(row['search_text'],0)+1
  if len(selected)>=k:break
 return selected
def main():
 p=argparse.ArgumentParser();p.add_argument('query',nargs='?');p.add_argument('--index',action='store_true');p.add_argument('--lexical',action='store_true');p.add_argument('--curated',action='store_true');p.add_argument('-k',type=int,default=12);p.add_argument('--max-length',type=int,default=40);p.add_argument('--json',action='store_true');a=p.parse_args()
 if a.index:index();return
 if not a.query:p.error('Supply an emotion-shaped query or --index')
 if a.k<1:p.error('-k must be positive')
 out=search(a.query,a.k,a.max_length,a.curated,a.lexical)
 if a.json:print(json.dumps(out,ensure_ascii=False,indent=2))
 else:
  for r in out:print(f"{r['face']}  [{r['score']:.3f}]\n  {r['description']}\n  ({r['annotation_kind']})")
if __name__=='__main__':main()
