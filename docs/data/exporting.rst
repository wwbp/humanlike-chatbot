Exporting Data
==============

ChatbotLab provides multiple ways to export conversation and participant data
for analysis.

Admin Exports
-------------

From the admin interface, select a model, study, or participant range and
choose:

- **CSV Export:** Tabular data suitable for R, Python, or Excel
- **JSON Export:** Structured data for downstream scripts
- **ZIP Archive:** Full session data including logs
- **Programmatic Export:** Use Django ORM or custom scripts to export data from
  the backend.

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
       writer.writerow(["conversation_id", "participant_id", "start_time"])
       for convo in Conversation.objects.all():
           writer.writerow([convo.id, convo.participant_id, convo.start_time])

Privacy and Ethics
------------------

Always anonymize participant identifiers and remove sensitive metadata before
sharing data. Align exports with your IRB's data management plan.
