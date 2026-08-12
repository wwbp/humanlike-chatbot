# Synthetic Data — Not Real Participants

Everything in this folder is **synthetic**, generated with the Anthropic API
(`claude-opus-5`). No real study, no real participants, no real PHQ-9 scores.
It exists solely to give the [documentation tutorials](../docs/analysis/)
real data to run against.

Each "person" speaker is a fabricated persona (age, gender, a one-line
backstory, and a PHQ-9 score) invented to produce plausible-looking
person↔AI conversations. Do not cite, publish, or reuse any of this as
findings about real people.

## Contents

- `convokit/` — the corpus in [ConvoKit](https://convokit.cornell.edu/)'s
  native format (`index.json`, `utterances.jsonl`, `speakers.json`,
  `conversations.json`). Used by [`docs/analysis/convokit.rst`](../docs/analysis/convokit.rst).
- `text/` — the same corpus flattened into a DLATK-style export
  (`msgs.csv`, `outcomes.csv`), used by [`docs/analysis/text.rst`](../docs/analysis/text.rst).
- `to_dlatk_format.py` — regenerates `text/` from `convokit/`.
