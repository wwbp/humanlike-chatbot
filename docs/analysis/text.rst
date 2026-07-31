text (R)
========

Overview
--------

The **R `text` package** wraps transformer language models (e.g. BERT) for
psychological and behavioral text analysis — embedding text, training models
on top of embeddings, and visualizing how words relate to numeric outcome
variables. This tutorial reproduces the `Supervised Dimension Projection
(SDP) <https://r-text.org/reference/textProjectionPlot.html>`_ workflow from
the package's `Psychological Methods tutorial
<https://r-text.org/articles/psychological_methods.html>`_, applied to the
same synthetic ChatbotLab corpus used in the :doc:`convokit` tutorial: 19
person↔AI conversations, each "person" speaker tagged with ``age``,
``gender``, ``persona``, and a **PHQ-9** depression-severity score.

Where the ConvoKit tutorial split speakers into two discrete groups and
compared n-gram frequencies, this tutorial projects individual words onto
PHQ-9 as a continuous dimension using contextual embeddings — a
complementary view of the same question.

Which Export Format?
---------------------

``textEmbed()`` and ``textProjection()`` expect a flat, rectangular data
frame: one row per text unit (e.g. one row per participant), with a text
column and numeric covariate columns aligned to it. That is exactly DLATK's
data model — a message-level table (``message_id``, ``user_id``,
``message``) plus a group-level outcomes table (``user_id``, outcome
columns) — not ConvoKit's turn-graph export, which links speakers,
conversations, and utterances by ``reply_to`` and has to be flattened before
a tool like ``text`` can use it.

So for ``text``, export from ChatbotLab in **DLATK format**, not ConvoKit
format. This repo only ships the ConvoKit export, so
``conversation_data/to_dlatk_format.py`` derives the DLATK-shaped tables from
it once, writing:

.. code-block:: text

   conversation_data/
     convokit/          # used by the ConvoKit tutorial
     text/
       msgs.csv         # message_id, user_id, timestamp, message
       outcomes.csv     # user_id, age, gender, persona, phq9

Only "person" utterances are included — the assistant has no outcome
variables attached to it. If ChatbotLab exports DLATK format directly for
your study, you'd start from that CSV pair and skip straight to the next
section.

Setup
-----

.. code-block:: r

   install.packages("text")
   library(text)

   # One-time: creates a Python environment with torch + transformers
   textrpp_install()
   textrpp_initialize()

Loading and Preparing the Data
--------------------------------

``textProjection`` needs one row per participant: their full conversation
text alongside their PHQ-9 score. Join the messages to the outcomes table
and collapse each participant's messages (in timestamp order) into a single
string:

.. code-block:: r

   library(dplyr)
   library(readr)

   msgs <- read_csv("conversation_data/text/msgs.csv")
   outcomes <- read_csv("conversation_data/text/outcomes.csv")

   person_data <- msgs %>%
     arrange(user_id, timestamp) %>%
     group_by(user_id) %>%
     summarise(text = paste(message, collapse = " ")) %>%
     inner_join(outcomes, by = "user_id")

This gives a 19-row data frame — one row per participant — with a ``text``
column (their full conversation) and their ``phq9``, ``age``, ``gender``,
and ``persona``.

Embedding the Text
-------------------

.. code-block:: r

   word_embeddings <- textEmbed(
     person_data$text,
     model = "bert-base-uncased",
     aggregation_from_tokens_to_word_types = "mean",
     keep_token_embeddings = FALSE
   )

``word_embeddings$texts$texts`` holds one BERT embedding per participant
(mean-aggregated across their tokens); ``word_embeddings$word_types$texts``
holds one decontextualized embedding per unique word type across the whole
corpus — both are required by ``textProjection``.

Supervised Dimension Projection
---------------------------------

.. code-block:: r

   projection_results <- textProjection(
     words = person_data$text,
     word_embeddings = word_embeddings$texts$texts,
     word_types_embeddings = word_embeddings$word_types$texts,
     x = person_data$phq9,
     split = "mean",
     min_freq_words_test = 2
   )

With only 19 participants, a mean split (10 participants above, 9 at or
below the mean PHQ-9 of 11.6) is more stable than the package's default
quartile split. ``min_freq_words_test = 2`` drops words that occur only
once, which would otherwise dominate the extremes on a corpus this small.

Plotting
--------

.. code-block:: r

   plot_projection <- textProjectionPlot(
     word_data = projection_results,
     min_freq_words_plot = 2,
     plot_n_word_extreme = 8,
     plot_n_word_frequency = 4,
     plot_n_words_middle = 2,
     y_axes = FALSE,
     p_alpha = 1,
     title_top = "Supervised Dimension Projection of PHQ-9",
     x_axes_label = "Low vs. High PHQ-9 score",
     p_adjust_method = "none"
   )

   plot_projection$final_plot

.. image:: /_static/text_projection_phq9.png
   :alt: Supervised Dimension Projection scatter plot showing words positioned from low to high PHQ-9, with words like "alright" and "ok" on the low end and "feel" and "just" on the high end
   :width: 100%

Each point is a word type positioned along the PHQ-9 dimension (x-axis);
``y_axes = FALSE`` keeps this to the 1-dimensional case, since we're only
projecting onto one variable. Point size scales with word frequency; the
most extreme and most frequent words on each side are labeled.

Results
-------

Top words toward **higher** PHQ-9 (by Supervised Dimension Projection score):

.. list-table::
   :header-rows: 1

   * - word
     - n
     - SDP
     - Cohen's d
     - p
   * - feel
     - 17
     - 2.12
     - 2.18
     - .054
   * - just
     - 98
     - 1.71
     - 1.72
     - .111
   * - i
     - 325
     - 1.66
     - 1.67
     - .114
   * - or
     - 16
     - 1.52
     - 1.51
     - .164
   * - feels
     - 17
     - 1.50
     - 1.48
     - .182
   * - really
     - 28
     - 1.46
     - 1.44
     - .207
   * - even
     - 9
     - 1.41
     - 1.38
     - .237

Top words toward **lower** PHQ-9:

.. list-table::
   :header-rows: 1

   * - word
     - n
     - SDP
     - Cohen's d
     - p
   * - alright
     - 36
     - -3.13
     - -3.70
     - < .001
   * - ok
     - 99
     - -3.08
     - -3.65
     - < .001
   * - !
     - 16
     - -2.82
     - -3.36
     - < .001
   * - chat
     - 4
     - -2.42
     - -2.91
     - .007
   * - conversation
     - 5
     - -2.28
     - -2.75
     - .018
   * - man
     - 16
     - -2.23
     - -2.70
     - .019

The direction agrees with the ConvoKit Fighting Words tutorial on the same
corpus: affect and hedging words (``feel``, ``feels``, ``just``) skew toward
higher PHQ-9, while upbeat, closing-out words (``alright``, ``ok``, ``man``)
skew toward lower PHQ-9 — two different toolkits converging on the same
pattern. Note the asymmetry, though: only the low-PHQ-9 words clear
``p < .05`` (uncorrected) here. With just 19 participants this is a workflow
demonstration, not a finding — treat the plot and tables as a template to
re-run on a properly powered study export, at which point you'd also want
``p_adjust_method`` set to something other than ``"none"``.

Generalizing
------------

Swap ``phq9`` for any other outcome column in ``outcomes.csv`` — age, a
REDCap or Qualtrics field passed through at
:doc:`../survey-integration/index`, or a score from your own instrument —
and the rest of the pipeline (``textEmbed`` → ``textProjection`` →
``textProjectionPlot``) is unchanged. The same embeddings also feed
``textTrain``/``textPredict`` if you want a predictive model instead of a
projection plot.
