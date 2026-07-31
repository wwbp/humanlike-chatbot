ConvoKit
========

Overview
--------

**ConvoKit** is a Python toolkit for computational analysis of conversations,
built by Cornell's Conversational Analysis Toolkit team. This tutorial loads
a ChatbotLab conversation export into ConvoKit and applies the **Fighting
Words** module. Fighting Words finds the words that most distinguish two
groups of text. Here, we use it to compare participants with higher and
lower PHQ-9 depression scores.

The example runs on the synthetic corpus in ``conversation_data/convokit/``.
This corpus contains 19 synthetic person-to-AI conversations. Each "person"
speaker is tagged with ``age``, ``gender``, ``persona``, and ``phq9``. Swap
in an export from your own study to reproduce the same workflow. A flattened
version of this same corpus is used in the :doc:`text` tutorial.

Setup
-----

.. code-block:: bash

   pip install convokit

Loading the Data
-----------------

ChatbotLab exports conversations in ConvoKit's native corpus format:
``index.json``, ``utterances.jsonl``, ``speakers.json``, and
``conversations.json``. No conversion is needed. Point ``Corpus`` at the
export directory:

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

We split the "person" speakers into two groups using a median split on
PHQ-9. We then tag every utterance with its speaker's group:

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

The median PHQ-9 in this corpus is 12. This gives 10 higher-symptom speakers
(PHQ-9 at or above 12) and 9 lower-symptom speakers (PHQ-9 below 12),
covering 762 "person" utterances. We exclude assistant turns, since the
comparison is about how participants talk, not the bot.

Running Fighting Words
-----------------------

`Fighting Words <https://convokit.cornell.edu/documentation/fightingwords.html>`_
uses a Dirichlet-multinomial model to find the n-grams that most distinguish
two groups of text. It corrects for the noise that plain frequency counts
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

``result`` is a DataFrame of every n-gram with a z-score. Positive values
are characteristic of ``higher_symptom`` speech. Negative values are
characteristic of ``lower_symptom`` speech. Setting ``plot=True`` also
renders ConvoKit's built-in scatter plot. The plot shows the weighted
log-odds ratio (z-score) on the y-axis against how often each n-gram occurs,
on a log-scaled x-axis. Marker size scales with the size of the z-score.
Color marks the class. The most significant n-grams on each side are
labeled.

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

Higher-PHQ-9 speakers use more affect language, such as ``feel``, ``feels``,
and ``nothing``. They also use more hedging language, such as ``just`` and
``don`` (from "don't"). Lower-PHQ-9 speakers use more upbeat, closing
language, such as ``good``, ``alright``, ``ok``, and ``ha``.

With only 19 speakers, the z-scores are modest. All magnitudes are under 3.
Treat this as a demonstration of the workflow, not a finding. Re-run the
same code on a full study export for a properly powered comparison.

Generalizing
------------

This method is not specific to PHQ-9. Split speakers or utterances on any
field in ``speaker.meta`` or ``conversation.meta``, such as ``persona``,
``age``, or a REDCap or Qualtrics field passed through at
:doc:`../survey-integration/index`. Then hand the two groups to a ConvoKit
transformer. This works for any other feature module ConvoKit ships, such
as politeness strategies, linguistic coordination, or prompt types, not
just Fighting Words.
