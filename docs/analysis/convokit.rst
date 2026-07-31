ConvoKit
========

Analyze conversational structure and interactional dynamics using **ConvoKit**,
a Python toolkit for computational analysis of conversations built by Cornell's
Convokit team. This tutorial loads a ChatbotLab conversation export straight
into ConvoKit and uses ConvoKit's **Fighting Words** module to find the
language that most distinguishes participants by a survey variable — here,
PHQ-9 depression-severity score.

The example below runs end-to-end on the synthetic corpus shipped in
``conversation_data/convokit/`` (19 synthetic person↔AI conversations, each
"person" speaker tagged with ``age``, ``gender``, ``persona``, and ``phq9``).
Swap in an export from your own study to reproduce the same workflow. A
flattened version of this same corpus, exported in DLATK format, is used in
the :doc:`text` tutorial.

Setup
-----

.. code-block:: bash

   pip install convokit

Loading a ChatbotLab Export
----------------------------

ChatbotLab's conversation exports are already written in ConvoKit's native
corpus format (``index.json``, ``utterances.jsonl``, ``speakers.json``,
``conversations.json``), so no conversion step is needed — point ``Corpus``
at the export directory:

.. code-block:: python

   from convokit import Corpus, FightingWords

   corpus = Corpus(filename="conversation_data/convokit")
   corpus.print_summary_stats()

.. code-block:: text

   Number of Speakers: 20
   Number of Utterances: 1543
   Number of Conversations: 19

Every "person" speaker carries the survey metadata collected alongside the
conversation:

.. code-block:: python

   speaker = corpus.get_speaker("user_00001")
   print(speaker.id, speaker.meta)

.. code-block:: text

   user_00001 {'role': 'person', 'age': 28, 'gender': 'man',
               'persona': 'small business owner, the business is struggling',
               'phq9': 7}

Grouping Speakers by PHQ-9
---------------------------

Split the "person" speakers into a higher- and lower-symptom group using a
median split on PHQ-9, then tag every utterance with its speaker's group:

.. code-block:: python

   import statistics

   person_speakers = [s for s in corpus.iter_speakers() if s.meta.get("role") == "person"]
   median = statistics.median(s.meta["phq9"] for s in person_speakers)

   def group(speaker):
       if speaker.meta.get("role") != "person":
           return None
       return "higher_symptom" if speaker.meta["phq9"] >= median else "lower_symptom"

   for utt in corpus.iter_utterances():
       utt.meta["symptom_group"] = group(corpus.get_speaker(utt.speaker.id))

On this corpus the median PHQ-9 is **12**, giving 10 higher-symptom speakers
(PHQ-9 ≥ 12) and 9 lower-symptom speakers (PHQ-9 < 12), covering 762 "person"
utterances (assistant turns are excluded — the comparison is about how
participants talk, not the bot).

Running Fighting Words
-----------------------

`Fighting Words <https://convokit.cornell.edu/documentation/fightingwords.html>`_
uses a Dirichlet-multinomial model to find the n-grams that most distinguish
two groups of text, correcting for the noise that plain frequency counts
produce on small samples:

.. code-block:: python

   fw = FightingWords(ngram_range=(1, 2))
   fw.fit(
       corpus,
       class1_func=lambda u: u.meta.get("symptom_group") == "higher_symptom",
       class2_func=lambda u: u.meta.get("symptom_group") == "lower_symptom",
   )

   result = fw.summarize(
       corpus, plot=True, class1_name="higher_symptom", class2_name="lower_symptom"
   )

``result`` is a DataFrame of every n-gram with a z-score: positive values are
characteristic of ``higher_symptom`` speech, negative values of
``lower_symptom`` speech. Passing ``plot=True`` additionally renders
ConvoKit's built-in fighting-words scatter plot — weighted log-odds ratio
(z-score) on the y-axis against how often each n-gram occurs, on a log-scaled
x-axis. Marker size scales with the z-score's magnitude, color marks the
class, and the most significant n-grams for each side are labeled.

.. image:: /_static/convokit_fighting_words.png
   :alt: Scatter plot of weighted log-odds ratio vs. word frequency, showing n-grams distinguishing higher- and lower-PHQ-9 speakers
   :width: 100%

Results
-------

Top n-grams toward the **higher-symptom** group:

.. list-table::
   :header-rows: 1

   * - n-gram
     - z-score
   * - bye
     - 2.20
   * - up
     - 1.97
   * - or
     - 1.83
   * - nothing
     - 1.70
   * - feels
     - 1.57
   * - feel
     - 1.57
   * - just
     - 1.45
   * - thing
     - 1.41
   * - don
     - 1.41
   * - he
     - 1.39

Top n-grams toward the **lower-symptom** group:

.. list-table::
   :header-rows: 1

   * - n-gram
     - z-score
   * - out
     - -2.88
   * - there
     - -1.80
   * - back
     - -1.80
   * - alright
     - -1.77
   * - one
     - -1.72
   * - the
     - -1.69
   * - ha
     - -1.65
   * - man
     - -1.53
   * - ok
     - -1.49
   * - good
     - -1.47

Even in this small, synthetic corpus, the direction of the effect is
sensible: higher-PHQ-9 speakers lean on affect language (``feel`` /
``feels``, ``nothing``) and hedging (``just``, ``don``\ 't), while
lower-PHQ-9 speakers lean toward upbeat, closing-out language (``good``,
``alright``, ``ok``, ``ha``). With only 19 speakers the z-scores are modest
(magnitudes under 3) and should be read as a workflow demonstration, not a
finding — re-run the same code on a full study export to get a properly powered
comparison.

Generalizing
------------

Nothing here is specific to PHQ-9. The same pattern — split speakers or
utterances on any field in ``speaker.meta`` or ``conversation.meta``
(``persona``, ``age``, a REDCap or Qualtrics field passed through at
:doc:`../survey-integration/index`), then hand the two groups to a ConvoKit
transformer — works for any other feature module ConvoKit ships (politeness
strategies, linguistic coordination, prompt types, and more), not just
Fighting Words.
