DLATK
=====

Overview
--------

**DLATK** (Differential Language Analysis ToolKit) is a Python toolkit for
correlating language with outcome variables. Differential Language Analysis
(DLA) is its signature method. DLA extracts language features, such as
n-grams, from a corpus, then correlates the frequency of each feature with
an outcome variable across participants.

We apply DLA to the same synthetic ChatbotLab corpus used in the other
tutorials in this section: 19 person-to-AI conversations, each "person"
tagged with a PHQ-9 depression score. We correlate single-word frequencies
with PHQ-9.

Data Format
-----------

DLATK reads from a SQL database. It expects two tables: a message table
(``message_id``, ``user_id``, ``message``) and an outcome table (``user_id``,
outcome columns). DLATK defaults to MySQL, but it also supports SQLite, so no
database server is required.

ChatbotLab exports conversation data in this shape already, as a SQLite
database with a ``msgs`` table and an ``outcomes`` table. We use that export
directly, at ``conversation_data/dlatk/dlatk.db``.

The message table can hold many rows per participant, one per message.
DLATK aggregates across whichever column is passed to ``-c`` (its alias is
``-g``) when it extracts features and runs correlations. Messages do not
need to be combined into one row per participant first.

Setup
-----

.. code-block:: bash

   pip install dlatk

Extracting Unigram Features
------------------------------

DLATK extracts n-gram features with ``--add_ngrams``. We extract unigrams
only, with ``-n 1``. DLATK's default is 1- to 3-grams, but with only 19
participants, most 2- and 3-grams occur too rarely to correlate with
anything. Unigrams give more participants a non-zero count per word, which
matters more than usual on a corpus this small:

.. code-block:: bash

   dlatkInterface.py --db_engine sqlite -d conversation_data/dlatk/dlatk \
     -t msgs -c user_id \
     --add_ngrams -n 1

This creates the feature table ``feat$1gram$msgs$user_id`` inside
``dlatk.db``.

Filtering Rare Features
-------------------------

Drop words used by too few participants, since a word only one person uses
cannot be a reliable correlate of anything:

.. code-block:: bash

   dlatkInterface.py --db_engine sqlite -d conversation_data/dlatk/dlatk \
     -t msgs -c user_id \
     -f 'feat$1gram$msgs$user_id' --feat_occ_filter --set_p_occ 0.05

This keeps 243 distinct unigrams, each used by at least 5% of participants.

Running Differential Language Analysis
-----------------------------------------

Correlate each of the 243 unigrams with PHQ-9:

.. code-block:: bash

   dlatkInterface.py --db_engine sqlite -d conversation_data/dlatk/dlatk \
     -t msgs -c user_id \
     -f 'feat$1gram$msgs$user_id$0_05' \
     --outcome_table outcomes --outcomes phq9 \
     --group_freq_thresh 50 \
     --correlate --csv --rmatrix --sort --no_correction \
     --output_name conversation_data/dlatk/dla_phq9

By default, DLATK corrects p-values for the number of features tested. With
243 features and 19 participants, that correction leaves nothing
significant. ``--no_correction`` turns it off, so the p-values below are
uncorrected. Treat them as exploratory, the same way we treat the z-scores
and SDP scores in the other two tutorials.

Word Clouds
-----------

Add ``--tagcloud --make_wordclouds`` to the same command to render the
significant words as word clouds, sized by effect size, instead of just
printing the correlation table:

.. code-block:: bash

   dlatkInterface.py --db_engine sqlite -d conversation_data/dlatk/dlatk \
     -t msgs -c user_id \
     -f 'feat$1gram$msgs$user_id$0_05' \
     --outcome_table outcomes --outcomes phq9 \
     --group_freq_thresh 50 \
     --correlate --csv --rmatrix --sort --no_correction \
     --tagcloud --make_wordclouds \
     --output_name conversation_data/dlatk/dla_phq9

This writes two PNGs to
``conversation_data/dlatk/dla_phq9_tagcloud_wordclouds/``, one per
direction of the correlation:

.. image:: /_static/dla_phq9_wordcloud_higher.png
   :alt: Word cloud of words positively correlated with higher PHQ-9, dominated by "that" and "weeks"
   :width: 48%

.. image:: /_static/dla_phq9_wordcloud_lower.png
   :alt: Word cloud of words negatively correlated with PHQ-9 (i.e. correlated with lower PHQ-9), dominated by "one" and "it'd"
   :width: 48%

Larger words have a larger absolute correlation with PHQ-9. The left cloud
is the same word list as the "higher PHQ-9" table below; the right cloud is
the "lower PHQ-9" table.

Results
-------

Words significantly correlated with **higher** PHQ-9, uncorrected p < .05:

.. list-table::
   :header-rows: 1

   * - word
     - r
     - p
     - freq
   * - that
     - 0.674
     - .0016
     - 51
   * - weeks
     - 0.586
     - .0083
     - 7
   * - just
     - 0.583
     - .0088
     - 98
   * - he
     - 0.513
     - .0247
     - 13
   * - maybe
     - 0.499
     - .0295
     - 42
   * - feels
     - 0.497
     - .0303
     - 17
   * - it
     - 0.464
     - .0453
     - 140
   * - make
     - 0.461
     - .0467
     - 6

Words significantly correlated with **lower** PHQ-9:

.. list-table::
   :header-rows: 1

   * - word
     - r
     - p
     - freq
   * - one
     - -0.589
     - .0080
     - 17
   * - it'd
     - -0.568
     - .0111
     - 4
   * - phone's
     - -0.550
     - .0147
     - 3
   * - gonna
     - -0.540
     - .0171
     - 20
   * - itself
     - -0.519
     - .0228
     - 4
   * - meaning
     - -0.510
     - .0256
     - 5
   * - actually
     - -0.503
     - .0281
     - 37

``just`` and ``feels`` correlate with higher PHQ-9 here, the same direction
found by ConvoKit's Fighting Words and the R text package's Supervised
Dimension Projection on this corpus. Three different methods point to the
same words.

With only 19 participants and no p-value correction, this is a
demonstration of the workflow, not a finding. Re-run this pipeline on a
properly powered study export, and drop ``--no_correction``.

Generalizing
------------

Swap ``phq9`` for any other column in ``outcomes.csv``, such as age, or a
REDCap or Qualtrics field passed through at
:doc:`../survey-integration/index`. DLATK also extracts features beyond raw
n-grams, including LIWC categories, LDA topics, and transformer embeddings,
any of which can replace the unigram feature table in the correlation step.
