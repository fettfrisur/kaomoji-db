"""Rebuild normalized catalogue. No Unicode compatibility normalization: shapes matter."""
import json, re, html, hashlib, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Interpretive English glosses, authored for retrieval; source labels remain intact.
GLOSSES={}
for group,description in [
 ('doya ehhen ninmari niyaniya','smug self satisfied pleased with myself mischievous knowing grin'),
 ('smile happy yorokobu yatta sumairu waai niconico nikkori yeay banzai','happy pleased cheerful joyful celebration delight'),
 ('muhuhu fufufu uhuhu guhehe sneaky waruikao','mischievous scheming sly chuckle playful menace'),
 ('akireru yareyare tameiki nigawarai','weary disbelief exasperated sigh resigned amused disappointment'),
 ('suyaa nemui neru good-night akubi futon','sleepy tired drowsy peaceful bedtime yawning'),
 ('shy hazukashii mojimoji tehe ehehe','bashful embarrassed shy sheepish self conscious'),
 ('cry sad shobon shonbori ochikkomu pien uruuru','sad crying downcast disappointed tearful vulnerable'),
 ('angry mukatsuku iraira punpun oko fuman pikipiki','angry annoyed grumpy irritated frustrated'),
 ('hug gyu dakitsuku nadenade yoshiyoshi iikoiiko iyashi odaijini','comfort affection reassurance hug gentle support patting'),
 ('love heart kiss chu meromero dokidoki kyun','love affectionate fondness romantic tenderness'),
 ('peek chirachira kakureru kosokoso','peeking hiding tentative curious shy watching'),
 ('surprise shock pokaan gaan nandato donbiki','surprised astonished shocked stunned disbelief'),
 ('hatena gimon wakaranai konwaku kubiwokashigeru kangaeru nayamu','confused puzzled questioning thinking uncertain curious'),
 ('magao sun jitome jii shirome','deadpan blank stare unimpressed skeptical flat expression'),
 ('salute aisatsu tewofuru good-morning konbanwa byebye','greeting waving hello goodbye salute'),
 ('ganbaru ouen fight furefure gutts-pose power','determined encouragement lets do this resolve effort'),
 ('thanks orei azasu bow dogeza sorry ayamaru sumimasen moushiwakenai','gratitude thanks apology bow humility'),
 ('relax hokkori yokatta yurui su','relaxed relieved calm content cozy quietly satisfied'),
 ('tired shindoi guttari gessori mendokusai','exhausted drained weary too much effort'),
 ('scary fear obieru gakuburu shinpai fuan','afraid worried anxious nervous trembling'),
 ('wakuwaku tanoshimi wakuteka ukiuki','excited anticipation eager looking forward'),
 ('understand naruhodo fumufumu nodding sorena','understanding agreement recognition thoughtful nod'),
 ('magic kiraan kirakira star pikapika','sparkling magical flourish wonder'),
 ('tobokeru tobokeru tehepero','feigned innocence cheeky evasive who me'),
 ('oteage owata muri','helpless resignation giving up overwhelmed'),
 ('cat nyaa nikukyuu','cat feline paws cute animal'),
 ('bear kuma','bear animal cuddly'),
 ('rabbit','rabbit bunny animal long ears'),
 ('music utau dance norinori','music singing dancing rhythmic enthusiasm'),
 ('writing memo benkyou pasokon','writing studying taking notes concentrating working'),
 ('chabudaigaeshi','table flip frustration dramatic rage'),
 ('ok iine good-job applause pachipachi','approval well done congratulations applause')]:
 for tag in group.split():GLOSSES[tag]=description
curated=[
 ('(￣ー￣)','A restrained closed-eye smile; quiet satisfaction, knowing confidence, or affectionate smugness.','smug knowing pleased quiet'),
 ('(￣▽￣)ゞ','A smiling face with a hand by its head; sheepish acknowledgement, good-humoured admission, or a casual salute.','sheepish acknowledgement salute'),
 ('(•̀ᴗ•́)و','A small determined smile with a raised fist; ready to tackle something, supportive resolve, enthusiastic competence.','determined encouragement ready'),
 ('(¬_¬)','A sideways flat stare; skeptical suspicion, dry disapproval, or amused side-eye.','skeptical side eye unimpressed'),
 ('(；￣ー￣)','A composed smile with a sweat mark; pretending everything is fine while privately apprehensive.','strained smile nervous awkward composure'),
 ('(｡•́︿•̀｡)','A small downturned face; soft disappointment, tender concern, or a vulnerable request for comfort.','sad vulnerable gentle'),
 ('(っ˘ω˘ς )','Closed eyes with hands gathered around the face; cozy contentment and quiet delight.','cozy content peaceful pleased'),
 ('(⊙_⊙)','Wide round eyes and a flat mouth; stunned silence, abrupt realization, or incredulous attention.','stunned surprise disbelief'),
 ('┐(￣ヘ￣)┌','A shrug with a displeased mouth; resigned exasperation, what can you do, mildly theatrical helplessness.','resigned exasperated shrug'),
 ('(ง •̀_•́)ง','Two raised fists and a focused face; bracing for a challenge, mock combat, or determined encouragement.','determined fight resolve'),
 ('|･ω･)','A small face peeking around an edge; tentative curiosity, quietly checking in, or bashful interest.','peeking curious tentative'),
 ('(－_－) zzZ','Closed eyes with sleep marks; sleepy withdrawal, bedtime calm, or playful boredom.','sleepy tired peaceful'),
 ('(ノಠ益ಠ)ノ彡┻━┻','A furious face throwing a table; exaggerated frustration and comic loss of patience.','table flip angry frustrated'),
 ('┬─┬ノ( º _ ºノ)','A figure carefully restoring a table; comic de-escalation, tidying up after chaos, patient repair.','restore table calm repair de escalation'),
 ('(づ｡◕‿‿◕｡)づ','A smiling face with outstretched arms; offering a warm hug and uncomplicated affection.','hug comforting warm'),
 ('(눈_눈)','Heavy-lidded eyes over a flat mouth; sustained unimpressed scrutiny, dry skepticism, or weary judgment.','deadpan skeptical unimpressed'),
 ('(๑˃̵ᴗ˂̵)و','A tightly smiling face with a fist; delighted success, a little victory, or eager encouragement.','victory delighted happy'),
 ('(╥﹏╥)','Streaming eyes with a wavering mouth; overt sadness, overwhelmed tenderness, or theatrical weeping.','crying sad overwhelmed'),
 ('(・・?)','A small face and question mark; mild puzzlement or politely asking for clarification.','confused puzzled questioning'),
 ('( ˘⌣˘)♡','A relaxed closed-eye smile with a heart; quiet fondness, tender approval, or affectionate contentment.','affection fondness peaceful'),
 ('(¬‿¬)','Sideways eyes with a smile; conspiratorial amusement, playful scheming, or a knowingly cheeky suggestion.','mischievous conspiratorial smug'),
 ('(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧','A wide happy face throwing sparkles; exuberant presentation, magical flourish, or gleeful celebration.','celebration magical sparkles'),
 ('(￣^￣)ゞ','A firm closed-eye expression and salute; acknowledging the task with mock solemnity and resolve.','salute acknowledgement determined'),
 ('(；・∀・)','A smiling face with a sweat mark; awkward cheerfulness, startled politeness, or nervously keeping up.','awkward nervous smile'),
 ('(つω`｡)','A face with a hand near a tearful eye; shy sadness, wiping away a tear, or touched emotion.','tearful touched shy'),
 ('( ´_ゝ`)','A lopsided understated face; dry detachment, wry amusement, or a quietly dismissive reaction.','wry detached dry deadpan'),
 ('٩(ˊᗜˋ*)و','An open smiling face with raised arms; energetic joy, celebration, and uncomplicated encouragement.','joy celebration encouragement'),
 ('(。-ω-)','Lowered eyes and a small mouth; drowsy composure, quiet retreat, or low-energy acceptance.','drowsy calm low energy'),
 ('(ʘ‿ʘ)','Round staring eyes above a smile; intent cheerful attention that can read as comic, slightly alarming eagerness.','eager intense alarming smile'),
 ('(╭ರ_•́)','A face with a raised brow-like flourish; theatrical scrutiny, detective-like curiosity, or suspicious consideration.','suspicious curious scrutiny')]
def main():
 rows={}
 def add(face,tag,url,kind='source'):
  face=html.unescape(face).strip()
  if not face:return
  row=rows.setdefault(face,{'id':hashlib.sha256(face.encode()).hexdigest()[:20],'face':face,'tags':[],'sources':[]})
  if tag not in row['tags']:row['tags'].append(tag)
  if url not in row['sources']:row['sources'].append(url)
 data=json.loads((ROOT/'sources/kaomoji.json').read_text())
 for tag,faces in data.items():
  for face in faces:add(face,tag,'https://github.com/kaomojiya-collection/kaomoji-collection')
 for tag,faces in json.loads((ROOT/'sources/kaomoji-you.json').read_text()).items():
  for face in faces:add(face,tag,'https://kaomoji.you/en/')
 for face,desc,tags in curated:
  for tag in tags.split():add(face,tag,'assistant-authored seed')
  rows[face]['description']=desc;rows[face]['annotation_kind']='individual interpretation'
 for row in rows.values():
  if 'description' not in row:
   gloss=list(dict.fromkeys(GLOSSES.get(t,t.replace('-',' ')) for t in row['tags']))
   cues=[];f=row['face']
   if any(c in f for c in '♡♥❤'):cues.append('heart symbol')
   if any(c in f for c in '✧✩✯★☆'):cues.append('star or sparkle ornament')
   if '?' in f or '？' in f:cues.append('question mark')
   if '┻' in f:cues.append('table-like object')
   if 'zzz' in f.lower():cues.append('sleep letters')
   row['description']='Source categories suggest: '+'; '.join(gloss)+('. Visible cues: '+', '.join(cues) if cues else '')+'.'
   row['annotation_kind']='category gloss plus literal cues; not individually reviewed'
  row['length']=len(row['face'])
  row['search_text']=row['description']+' Tags: '+' '.join(row['tags'])
 ordered=sorted(rows.values(),key=lambda r:r['id'])
 (ROOT/'catalogue.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in ordered))
 dbpath=ROOT/'catalogue.sqlite';dbpath.unlink(missing_ok=True)
 db=sqlite3.connect(dbpath)
 db.execute('CREATE TABLE kaomoji(id TEXT PRIMARY KEY, face TEXT UNIQUE, description TEXT, tags TEXT, sources TEXT, annotation_kind TEXT, length INTEGER)')
 db.executemany('INSERT INTO kaomoji VALUES(?,?,?,?,?,?,?)',[(r['id'],r['face'],r['description'],json.dumps(r['tags'],ensure_ascii=False),json.dumps(r['sources']),r['annotation_kind'],r['length']) for r in ordered])
 db.execute('CREATE VIRTUAL TABLE kaomoji_fts USING fts5(id UNINDEXED, description, tags)')
 db.executemany('INSERT INTO kaomoji_fts VALUES(?,?,?)',[(r['id'],r['description'],' '.join(r['tags'])) for r in ordered]);db.commit();db.close()
 print(json.dumps({'unique_faces':len(ordered),'source_categories':len(data),'individual_annotations':len(curated),'unique_search_texts':len(set(r['search_text'] for r in ordered))}))
if __name__=='__main__':main()
