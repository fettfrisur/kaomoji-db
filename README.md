# kaomoji-db — expressive candidate retrieval

A prototype catalogue for an assistant to find several possible expressions from an emotion-shaped query, then choose the face itself in context. Built 2026-09-28.

## Contents and annotation honesty

- 36,625 unique Unicode strings after exact deduplication and HTML entity decoding.
- Kaomojiya: 535 source categories; source snapshot and MIT license included.
- kaomoji.you: 831 entries in 39 groups before merging; extracted faces and labels included, not the site's explanatory prose.
- 30 individually interpreted seed faces, with descriptions written for this prototype.
- Remaining descriptions are category glosses with a few literal character cues, explicitly marked **not individually reviewed**. These are not 36,625 independent nuanced readings.
- Original category labels and source URLs are retained. Many Japanese romanized labels still lack English glosses, so retrieval quality varies by category.
- Original spacing and Unicode codepoints are preserved after trimming outer whitespace and decoding HTML entities. No NFKC normalization is used. Near-duplicates remain deliberately: tiny changes can change the expression.
- The collection includes decorative symbols, messages, and objects as well as faces. Short single-line results are preferred through filters; quality is not guaranteed by source membership.

## Quick start

```sh
git clone https://github.com/fettfrisur/kaomoji-db.git
cd kaomoji-db
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\activate` instead.


Use Python 3.11 or newer for the pinned semantic-search dependencies. Keyword search needs only Python's standard library with SQLite FTS5 support:

```sh
python build.py
python query.py 'smug quietly pleased' --lexical -k 12
```

For semantic retrieval:

```sh
python -m pip install -r requirements.txt
python build.py
python query.py --index
python query.py 'a little embarrassed but pleased that it worked' -k 12
python query.py 'patiently restoring order after comic chaos' --curated -k 6
python query.py 'quiet skeptical side eye' --max-length 20 --json
```

The model is `sentence-transformers/all-MiniLM-L6-v2`, run on CPU through FastEmbed/ONNX Runtime. First use downloads model files from Hugging Face into `.cache/embeddings/` (gitignored). Set `KAOMOJI_MODEL_CACHE` to use another location. `query.py` sets `ORT_DISABLE_TELEMETRY=1` before importing the runtime, as documented by Microsoft, and disables Hugging Face telemetry. It does not call a paid embedding API. Model weights are not included in this repository. The generated index contains 384-dimensional normalized vectors; query-time encoding still requires the model.

SQLite stores faces and metadata; a compressed NumPy matrix stores one vector per distinct search text, shared by faces with identical descriptions. This saves work without inventing semantic distinctions. Cosine similarity ranks candidates. A small bonus breaks close ties in favour of individual annotations. Character similarity and a per-description cap diversify the shortlist. Scores are similarity measurements, not calibrated emotion probabilities. There is no negative-clause parser: queries like “happy but not smug” still require contextual judgment.

`--curated` restricts retrieval to individually annotated seeds. `--lexical` is an explicit keyword fallback, not a semantic model. Unknown keyword searches return no results. JSON output includes source and annotation status for every candidate.

## Rebuild and extend

`python build.py` rebuilds JSONL and SQLite from source snapshots plus the curated descriptions in `build.py`. It does not access the network. Re-run `python query.py --index` after changes; catalogue fingerprints prevent use of stale vectors.

For substantial enrichment, add a separate reviewed annotation file rather than expanding the seed list indefinitely. Recommended fields:

- literal visual description (eyes, mouth, arms, props)
- several plausible emotional readings
- conversational intent (acknowledgement, reassurance, teasing, disbelief)
- valence, intensity, warmth, confidence, arousal, theatricality
- usage examples and counterexamples
- annotation author/model, version, review state, confidence
- source provenance and any ambiguity

Embed descriptions and short usage examples, rather than trusting an embedding model to interpret the raw glyphs. Treat source categories as evidence, not ground truth. Generate drafts in batches, review a sample, and improve the most-used candidates first. A broad low-confidence pool plus a smaller rich annotated pool is more useful than mass-produced near-identical prose.

Suggested assistant workflow: formulate the intended tone → retrieve 12–20 candidates → inspect actual shapes → select, adapt, or use none. The search result must never mandate the final expression. No fixed emoji frequency, random insertion, or automatic preference learning is implied.

## Integration status

This repository is a working local catalogue and query program, not an installed ChatGPT plugin or remote MCP server. It does not automatically load in every conversation. For durable assistant use, package it in an explicitly discoverable skill/plugin or expose the search function through an MCP tool. Suggested interface:

`search_kaomoji(intent: str, limit: int = 12, max_length: int = 40, reviewed_only: bool = False)`

An MCP service can keep the embedding model and matrix warm between requests. A skill-based local workflow can run the command above. Both should return candidate descriptions, original faces, sources and review status. The repository contains no credentials and starts no background service.

## Sources

- https://kaomoji.you/en/ — user-suggested starting page; extracted glyphs and category labels only. No blanket license is claimed for its collection.
- https://github.com/kaomojiya-collection/kaomoji-collection — category JSON; MIT license in `sources/LICENSE`. Upstream attributes the compilation to https://kaomojiya.org/.
- https://github.com/ekohrt/emoticon_kaomoji_dataset — discovered alternative advertising 62,000 tagged emoticons; **not imported**.
- https://qdrant.github.io/fastembed/ — embedding runtime documentation.
- https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md — process-lifetime telemetry opt-out.

The code and new descriptions in this prototype may be freely adapted; source data retains its own provenance and terms. The generated English glosses and descriptions are interpretations, not authoritative translations or a standard dictionary of meaning.

## Development checks

```sh
python check.py
```

Checks catalogue uniqueness, required metadata, SQLite integrity, keyword search, and (when `vectors.npz` is present) five semantic queries. Results are written to `validation.json`. The checked-in report is the initial prototype run, not a benchmark or a guarantee of semantic accuracy.

The source snapshots and individual annotations are committed. Generated `catalogue.jsonl`, `catalogue.sqlite`, and `vectors.npz` are gitignored: create them with `python build.py` and `python query.py --index`. Rebuild them after editing the source snapshots or annotations. Model weights and virtual environments are also not committed.
