REDCap Integration
==================

Overview
--------

Use ChatbotLab to embed conversational tasks directly into your REDCap data
collection instruments. Each REDCap form can display the ChatbotLab chat window
within a **Descriptive Text** field using an iframe.

.. important::

   REDCap must allow HTML and JavaScript in Descriptive Text fields.
   Some institutions disable this for security reasons. Contact your
   REDCap administrator if iframes are not permitted.

Data Needed to Embed Bot
------------------------

Record ID
^^^^^^^^^

REDCap automatically assigns each participant a unique ``record_id``.
This is available as a built-in variable and can be passed to ChatbotLab
to identify conversations.

In ChatbotLab, ``record_id`` serves the same purpose as Qualtrics's
``ResponseID``.

Bot Name
^^^^^^^^

1. In the ChatbotLab admin panel, navigate to **CHATBOT → Bots**.
2. Find the bot you wish to embed.
3. Copy its **Name** from the table.
4. Replace ``<BOT-NAME>`` in the iframe URL below.

Study Name
^^^^^^^^^^

Define a short descriptive name for your study, for example ``therapy_bot``.
This will be stored in the ChatbotLab database under ``study_name`` for tracking.

Participant ID (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^

If your REDCap project includes a custom participant ID field, you can
reference it in the iframe using a REDCap variable such as ``[participant_id]``.

If you do not have a custom field, you can rely on ``[record-id]`` as the
participant identifier.

Embedding ChatbotLab
---------------------

1. Deploy ChatbotLab on AWS following the :doc:`/deployment/index` guide.
2. In your REDCap project, open the desired instrument in the **Online Designer**.
3. Add a new **Descriptive Text** field.
4. Click the **pencil icon** to edit the field.
5. In the **Field Label** box, click the **“<>” (HTML)** icon and paste this code:

   .. code-block:: html

      <iframe
         src="https://<YOUR-CHATLAB-DOMAIN>/conversation?
              bot_name=<BOT-NAME>
              &conversation_id=[record-id]
              &participant_id=<PARTICIPANT-ID>
              &survey_id=[]
              &study_name=<STUDY-NAME>"
         width="100%"
         height="600"
         frameborder="0"
         style="border: none; overflow: hidden;">
      </iframe>

6. Replace the placeholders:

   - ``<BOT-NAME>``: your bot's name
   - ``<STUDY-NAME>``: your chosen study label
   - ``<SURVEY-ID>``: your unique REDCap survey identifier
   - ``<YOUR-CHATLAB-DOMAIN>``: your ChatbotLab domain, from deployment
   - ``<PARTICIPANT-ID>`` (optional): unique identifier for participants

7. Save and preview the form to verify that the chat window loads correctly.

Passing Data
------------

ChatbotLab automatically logs any metadata passed via URL parameters:

- ``participant_id``: usually ``[record-id]`` or a custom ID field
- ``study_name``: study descriptor
- ``bot_name``: determines which ChatbotLab bot instance to use

Data Linking
------------

- Each conversation is stored with its associated REDCap record ID.
- Conversations are linked in ChatbotLab’s database by ``participant_id`` and ``study_name``.
- You can merge these logs with exported REDCap data using ``record_id``.

Keystrokes (Optional)
---------------------

To capture engagement metrics (time on page, keystrokes, focus changes),
you can insert an optional script field after the chat iframe.

.. code-block:: html

   <script>
     let pageStart = Date.now();
     let timeAway = 0;
     let awayStart = null;

     document.addEventListener("visibilitychange", function() {
       if (document.hidden) {
         awayStart = Date.now();
       } else if (awayStart) {
         timeAway += Date.now() - awayStart;
         awayStart = null;
       }
     });

     window.addEventListener("beforeunload", function() {
       const totalTime = Date.now() - pageStart;
       const payload = JSON.stringify({
         participant_id: "[record-id]",
         total_time_on_page: totalTime,
         total_time_away_from_page: timeAway
       });
       navigator.sendBeacon("https://chatlab.yourdomain.org/api/update_keystrokes/", payload);
     });
   </script>

This mirrors the Qualtrics example and sends timing data to ChatbotLab for
each participant.

Validation
----------

1. Test the form in **Data Entry** or **Survey Mode**.
2. Check your browser console for any loading or network errors.
3. Verify that a new conversation record appears in ChatbotLab’s admin panel.
4. Confirm that keystroke and timing data (if enabled) are logged.

Other Options
-------------

- You can add instructions or task descriptions above the iframe
  in the same **Descriptive Text** field.
- To randomize bots between participants, define a REDCap field
  (e.g., ``[bot_condition]``) and use it in the iframe:

  .. code-block:: html

     bot_name=[bot_condition]
