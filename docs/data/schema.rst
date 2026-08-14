Database Schema
===============

This document describes the database schema for ChatbotLab's backend.
The database is implemented in **MySQL** and stores information about
bots, conversations, utterances, and keystrokes. Each table is prefixed
with ``chatbot_`` and linked by foreign keys for data integrity.

Bots Table
----------

**Table name:** ``chatbot_bot``

This table defines each chatbot available in the system and stores
its configuration, prompt, and assigned model.

.. list-table::
   :header-rows: 1

   * - Column
     - Type / Key
     - Description
   * - ``id``
     - PK
     - Unique ID of the bot.
   * - ``name``
     - VARCHAR, unique
     - Descriptive name of the bot (must be unique). Use a ``-voice`` suffix
       to route to the voice-chat UI instead of text chat.
   * - ``prompt``
     - TEXT
     - Prompt describing how the bot should behave.
   * - ``ai_model``
     - FK → chatbot_model
     - The AI model (provider + model ID) this bot uses.
   * - ``model_type``, ``model_id``
     - VARCHAR
     - Legacy provider/model-ID fields, superseded by ``ai_model``; kept for
       migration compatibility and not read by the chat path.
   * - ``initial_utterance``
     - TEXT
     - Optional initial message sent when a conversation starts.
   * - ``avatar_type``
     - VARCHAR
     - ``none``, ``default``, or ``user`` (participant-provided avatar).
   * - ``avatar_prompt``
     - TEXT
     - Prompt used to generate the bot's avatar image; falls back to a
       default prompt when empty.
   * - ``chunk_messages``
     - BOOLEAN
     - If true, split responses into human-like chunks; if false, send each
       response as one block.
   * - ``humanlike_delay``
     - BOOLEAN
     - If true, apply human-like typing/reading delays; if false, show
       messages instantly.
   * - ``reading_words_per_minute``, ``reading_jitter_min``,
       ``reading_jitter_max``, ``reading_thinking_min``,
       ``reading_thinking_max``
     - FLOAT
     - Parameters controlling the simulated delay before the bot "reads" an
       incoming message, in seconds (jitter/thinking bounds) or words/minute.
   * - ``writing_words_per_minute``, ``writing_jitter_min``,
       ``writing_jitter_max``, ``writing_thinking_min``,
       ``writing_thinking_max``
     - FLOAT
     - Parameters controlling the simulated delay before the bot "writes"
       its reply, in seconds (jitter/thinking bounds) or words/minute.
   * - ``intra_message_delay_min``, ``intra_message_delay_max``
     - FLOAT
     - Delay range between chunked message parts, in seconds. Only applies
       when ``chunk_messages`` is true.
   * - ``min_reading_delay``
     - FLOAT
     - Minimum reading delay applied regardless of message length, in
       seconds.
   * - ``follow_up_on_idle``
     - BOOLEAN
     - If true, the bot sends follow-up messages when the participant goes
       idle.
   * - ``idle_time_minutes``
     - INT
     - Minutes of inactivity before a participant is considered idle.
   * - ``follow_up_instruction_prompt``
     - TEXT
     - Instructions used to generate follow-up messages while idle.
   * - ``recurring_followup``
     - BOOLEAN
     - If true, keep sending follow-ups for the duration of an idle period;
       if false, send at most one per idle period.
   * - ``max_transcript_length``
     - INT
     - Max messages included in the chat history sent to the LLM. ``0`` =
       current message only, positive = that many most recent messages,
       negative = unlimited.
   * - ``moderation_harassment``, ``moderation_harassment_threatening``,
       ``moderation_hate``, ``moderation_hate_threatening``,
       ``moderation_self_harm``, ``moderation_self_harm_instructions``,
       ``moderation_self_harm_intent``, ``moderation_sexual``,
       ``moderation_sexual_minors``, ``moderation_violence``,
       ``moderation_violence_graphic``
     - DECIMAL(3,2)
     - Per-category moderation thresholds (0.0-1.0, lower = stricter). See
       :doc:`../advanced-customization/moderation` for what each category
       means and how thresholds are applied.
   * - ``personas``
     - M2M → chatbot_persona
     - Personas this bot can embody, via the ``chatbot_bot_personas`` join
       table.

Conversations Table
-------------------

**Table name:** ``chatbot_conversation``

Stores high-level metadata for each chat session, including study context,
participant identifiers, and Qualtrics linkage.

.. list-table::
   :header-rows: 1

   * - Column
     - Type / Key
     - Description
   * - ``id``
     - PK
     - Auto-incremented unique ID for each conversation.
   * - ``conversation_id``
     - VARCHAR, unique
     - Response ID from Qualtrics (or equivalent) representing the unique
       session.
   * - ``bot_name``
     - VARCHAR
     - Name of the bot the participant interacted with. Stored as a plain
       string, not a foreign key to ``chatbot_bot`` — it isn't enforced
       against, or automatically updated by, later changes to that bot.
   * - ``bot_config``
     - TEXT (JSON)
     - Snapshot of the bot's configuration (model, personas, delay
       settings, etc.) captured when the conversation started. This is how
       "which model was actually used" survives later edits to the bot.
   * - ``participant_id``
     - VARCHAR
     - Participant ID (fetched from Qualtrics or Prolific).
   * - ``study_name``
     - VARCHAR
     - Optional name of the study.
   * - ``user_group``
     - VARCHAR
     - Qualtrics condition or randomized group assignment.
   * - ``started_time``
     - DATETIME
     - Timestamp when the conversation began.
   * - ``initial_utterance``
     - VARCHAR
     - The initial message if the bot began the conversation.
   * - ``survey_id``
     - VARCHAR
     - Qualtrics ``survey_id`` fetched via URL.
   * - ``survey_meta_data``
     - TEXT (JSON)
     - Full Qualtrics metadata payload received at start.
   * - ``selected_persona``
     - FK → chatbot_persona
     - The persona randomly selected for this conversation, if the bot has
       any personas configured; ``NULL`` otherwise.

---

Utterances Table
----------------

**Table name:** ``chatbot_utterance``

Each row corresponds to a single message (utterance) in a conversation.

.. list-table::
   :header-rows: 1

   * - Column
     - Type / Key
     - Description
   * - ``id``
     - PK
     - Unique ID for each utterance.
   * - ``speaker_id``
     - VARCHAR
     - Who sent the message: ``"user"`` or ``"assistant"`` on the main text-
       and follow-up-chat paths. The voice-chat path instead writes
       ``"participant"`` for the human side.
   * - ``bot_name``
     - VARCHAR
     - Name of the bot in this conversation.
   * - ``conversation_id``
     - FK → chatbot_conversation
     - Conversation foreign key.
   * - ``participant_id``
     - VARCHAR
     - Qualtrics or Prolific participant ID.
   * - ``text``
     - TEXT
     - Content of the utterance.
   * - ``created_time``
     - DATETIME
     - When the utterance was created.
   * - ``audio_file``
     - VARCHAR (URL)
     - Link to audio file stored in S3 (if applicable).
   * - ``is_voice``
     - BOOLEAN
     - Indicates whether the utterance includes voice (1 = True).
   * - ``instruction_prompt``
     - TEXT
     - System prompt (bot prompt + persona) sent to the LLM.
   * - ``chat_history_used``
     - TEXT (JSON)
     - Chat history that was actually passed to the LLM.
   * - ``moderation_category``
     - VARCHAR
     - Moderation category that blocked this exchange (e.g. ``harassment``);
       ``NULL`` when the message was not blocked.
   * - ``moderation_scores``
     - JSON
     - Full category → score map returned by the moderation API for a
       blocked message, including categories that passed. Recorded on the
       participant's row only; ``NULL`` otherwise.

.. note::

   When a message is blocked, no LLM call is made. Two rows are written: the
   participant's message and a fixed warning reply. Both carry
   ``moderation_category``, so ``WHERE moderation_category IS NOT NULL``
   returns the complete exchange; to exclude canned warnings from a
   transcript, drop the assistant rows where that column is set.
   ``moderation_scores`` is set on the participant's row only, since that is
   the message the scores describe. Blocks that predate these columns are
   labeled ``unknown`` — their real category and scores were never recorded.

---

Keystrokes Table
----------------

**Table name:** ``chatbot_keystroke``

Captures timing and engagement metrics for each chat session, providing
context about user attention and typing behavior.

.. list-table::
   :header-rows: 1

   * - Column
     - Type / Key
     - Description
   * - ``id``
     - PK
     - Unique ID for each keystroke record.
   * - ``conversation_id``
     - VARCHAR
     - Matches ``chatbot_conversation.conversation_id`` by convention, but
       is **not** a foreign key — keystroke logging can happen before a
       conversation row is registered, so there's no constraint tying the
       two together.
   * - ``total_time_on_page``
     - FLOAT
     - Time (in seconds) the participant spent on the chat page.
   * - ``total_time_away_from_page``
     - FLOAT
     - Time (in seconds) the participant was away from the page.
   * - ``keystroke_count``
     - INT
     - Number of keys pressed during the chat.
   * - ``timestamp``
     - DATETIME
     - When the keystroke data was recorded (set by the client, not
       auto-generated on write).

---

Schema Relationships
--------------------

- Each **conversation** references one **bot** via ``bot_name`` — a plain
  string match, not an enforced foreign key.
- Each **utterance** belongs to one **conversation**, via the real foreign
  key ``conversation_id``.
- Each **keystroke** record is associated with a conversation by matching
  ``conversation_id`` values, but this is not a foreign key relationship —
  see the note on the Keystrokes table above.
- Participants and studies can be linked across sessions by ``participant_id`` or ``study_name``.

.. note::

   ``moderation_category`` and ``moderation_scores`` on ``chatbot_utterance``
   are documented here as they will exist once PR #192 merges; they are not
   yet present on ``main``.

The diagram below abbreviates ``chatbot_bot`` to a representative subset of
columns for readability — see the full Bots Table above for all fields.

.. mermaid::

   erDiagram
      chatbot_bot ||..o{ chatbot_conversation : "bot_name (string match, not FK)"
      chatbot_conversation ||--o{ chatbot_utterance : "conversation_id (FK)"
      chatbot_conversation ||..o{ chatbot_keystroke : "conversation_id (string match, not FK)"

      chatbot_bot {
        int id PK
        varchar name UK
        text prompt
        int ai_model FK
        varchar model_id
        varchar model_type
        text initial_utterance
        varchar avatar_type
        text avatar_prompt
        boolean chunk_messages
        boolean humanlike_delay
        float reading_words_per_minute
        float writing_words_per_minute
        int max_transcript_length
        decimal moderation_harassment
      }

      chatbot_conversation {
        int id PK
        varchar conversation_id UK
        varchar bot_name
        text bot_config
        varchar participant_id
        varchar study_name
        varchar user_group
        datetime started_time
        varchar initial_utterance
        varchar survey_id
        text survey_meta_data
        int selected_persona FK
      }

      chatbot_utterance {
        int id PK
        varchar speaker_id
        varchar bot_name
        int conversation_id FK
        varchar participant_id
        text text
        datetime created_time
        varchar audio_file
        boolean is_voice
        text instruction_prompt
        json chat_history_used
        varchar moderation_category
        json moderation_scores
      }

      chatbot_keystroke {
        int id PK
        varchar conversation_id
        float total_time_on_page
        float total_time_away_from_page
        int keystroke_count
        datetime timestamp
      }

