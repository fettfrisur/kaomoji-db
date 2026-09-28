"""Structural integrity and retrieval smoke checks; writes an inspectable result report."""
import json,sqlite3,time
from pathlib import Path
import query
root=Path(__file__).resolve().parent
rows=query.catalogue()
assert len(rows)==len({r['face'] for r in rows})==len({r['id'] for r in rows})
assert all(r['description'] and r['sources'] and r['tags'] for r in rows)
db=sqlite3.connect(root/'catalogue.sqlite')
assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert db.execute('SELECT count(*) FROM kaomoji').fetchone()[0]==len(rows)
assert query.search('smug',lexical=True)
assert not query.search('qxzvnotaword',lexical=True)
report={'catalogue_rows':len(rows),'individual_annotations':sum(r['annotation_kind']=='individual interpretation' for r in rows),'checks':['exact deduplication','unique IDs','nonempty metadata','SQLite integrity','SQL/JSONL count agreement','keyword hit','unknown keyword miss'],'queries':[]}
if (root/'vectors.npz').exists():
 m=query.model()
 for text in ['quiet satisfaction with a little smugness','a little embarrassed but pleased that it worked','patiently restoring order after comic chaos','skeptical side eye','offering a gentle comforting hug']:
  start=time.perf_counter();hits=query.search(text,k=6,embedder=m)
  reviewed=query.search(text,k=4,curated=True,embedder=m)
  report['queries'].append({'query':text,'elapsed_seconds_two_searches':round(time.perf_counter()-start,3),'all_catalogue':[{'face':r['face'],'score':r['score'],'description':r['description'],'annotation_kind':r['annotation_kind']} for r in hits],'reviewed_only':[{'face':r['face'],'score':r['score'],'description':r['description']} for r in reviewed]})
(root/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
