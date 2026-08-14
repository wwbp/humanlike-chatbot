Viewing Data
============

You can review all collected conversation and participant data from the
**ChatbotLab Admin Panel** or by connecting to the database directly.

Admin Panel
-----------

Access the admin interface at:

``https://<your-domain>/api/admin``

Within the admin panel, you can browse:

- **Conversations:** One row per session, with a link through to its
  utterances (the full transcript)
- **Utterances:** Individual messages with timestamps
- **Bots and Personas:** Configuration metadata

There's no separate "Participants" section — participant identifiers
(survey response IDs, recruitment platform IDs) live as fields on
Conversations and Utterances, not a dedicated model.

Filtering
---------

The admin's filter sidebar differs by section:

- **Conversations:** bot name, user group, study name, start time, persona
- **Utterances:** voice flag, speaker (``user``/``assistant``), bot name,
  created time
- **Bots:** model provider, avatar type, and several boolean flags
  (chunking, humanlike delay, follow-up-on-idle, recurring follow-up)

Participant ID is **searchable** (the search box, not the filter sidebar)
on Conversations and Utterances. Keystrokes has no participant ID field at
all — it's only searchable/filterable by ``conversation_id`` and timestamp.

Export Options
--------------

From the admin interface, you can export a CSV or JSON snapshot of
conversation-level or utterance-level data.
