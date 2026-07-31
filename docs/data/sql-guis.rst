Accessing ChatbotLab Data via SQL GUIs
=======================================

For teams preferring graphical interfaces, ChatbotLab's MySQL database can be
accessed through popular SQL clients. This allows browsing, querying, and
exporting conversation data without writing SQL manually.

Supported Applications
----------------------

You can connect to ChatbotLab's database using:

- **Sequel Ace (macOS)**
- **Sequel Pro (macOS)**
- **HeidiSQL (Windows)**
- **MySQL Workbench (cross-platform)**

Connection Settings
-------------------

Use your AWS database credentials and instance details:

- **Host:** `<your-chatlab-db-endpoint>.rds.amazonaws.com`
- **Port:** `3306`
- **Username:** `chatlab_admin`
- **Password:** `<your_password>`
- **Database:** `chatlab_db`

Example (Sequel Ace)
~~~~~~~~~~~~~~~~~~~~

1. Open Sequel Ace → *New Connection*
2. Choose *Standard Connection*
3. Fill in:
   - Name: `ChatbotLab`
   - Host: `<your-db-endpoint>`
   - User: `chatlab_admin`
   - Password: `<your_password>`
   - Database: `chatlab_db`
4. Click *Connect*.

Security Notes
--------------

- Never expose database credentials publicly.  
- Restrict inbound connections to your organization's IPs via AWS Security Groups.  
- Use **read-only** users for analysis tasks when possible.

Query Examples
--------------

View all conversations:

.. code-block:: sql

   SELECT id, participant_id, start_time, end_time
   FROM conversation
   ORDER BY start_time DESC;

View recent utterances:

.. code-block:: sql

   SELECT conversation_id, speaker, text, created_at
   FROM utterance
   WHERE created_at > NOW() - INTERVAL 7 DAY;
