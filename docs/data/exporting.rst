Exporting Data
==============

ChatbotLab provides multiple ways to export conversation and participant data
for analysis.

Admin Exports
-------------

From the Conversations, Utterances, or Bots admin list, filter or search
down to the rows you want, then use the **Export** button to download them
as:

- **CSV:** Tabular data suitable for R, Python, or Excel
- **JSON:** Structured data for downstream scripts

Every field on the model is included automatically — there's no separate
list of exportable columns to maintain per table.

Beyond the admin UI, you can always write a script against the Django ORM
(see the example below) for exports that don't fit a simple filtered list —
joining across tables, custom formatting, or scheduled/automated runs.

Direct Database Exports
-----------------------

Developers can also export data directly from the MySQL database. Use:

.. code-block:: bash

   mysqldump -u <user> -p chatlab_db > chatlab_data.sql

Example Script
--------------

.. code-block:: python

   from chatbot.models import Conversation, Utterance
   import csv

   with open("conversations.csv", "w") as f:
       writer = csv.writer(f)
       writer.writerow(["conversation_id", "participant_id", "started_time"])
       for convo in Conversation.objects.all():
           writer.writerow([convo.conversation_id, convo.participant_id, convo.started_time])

Privacy and Ethics
------------------

Always anonymize participant identifiers and remove sensitive metadata before
sharing data. Align exports with your IRB's data management plan.
