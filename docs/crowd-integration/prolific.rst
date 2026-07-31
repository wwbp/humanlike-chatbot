Prolific Integration
====================

Overview
--------

ChatbotLab integrates with **Prolific** to link crowdworker identifiers
with your survey and conversation data. This ties every participant's chat
to their Prolific record, so datasets merge cleanly and the record serves as
a backup.

Prolific metadata (participant ID, study ID, and session ID) is stored in
ChatbotLab's backend database alongside the corresponding survey data.

Workflow Summary
----------------

To use ChatbotLab through Prolific:

1. **Create a Prolific study.**
2. **Set the study URL** to your Qualtrics or REDCap survey that contains ChatbotLab.
3. Prolific automatically appends the following URL parameters to your survey link:

   ``?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}``

4. In your survey, **store these parameters as embedded data fields.**
5. Include them in your survey integration code so they are passed to ChatbotLab.

   .. code-block:: javascript

      Qualtrics.SurveyEngine.addOnload(function() {
         ...
         var prolificParticipantID = "<PROLIFIC-PARTICIPANT-ID>";  // Prolific PID
         var prolificStudyID = "<PROLIFIC-STUDY-ID>";              // Prolific study ID
         var prolificSessionID = "<PROLIFIC-SESSION-ID>";          // Prolific session ID

         ...

         botURL += "&participant_id=" + encodeURIComponent(prolificParticipantID);
         botURL += "&prolific_study_id=" + encodeURIComponent(prolificStudyID);
         botURL += "&prolific_session_id=" + encodeURIComponent(prolificSessionID);
      });

Example (Qualtrics)
-------------------

To capture and pass Prolific IDs in **Qualtrics**:

1. Open your survey in Qualtrics.
2. Navigate to **Survey Flow → Add a New Element → Embedded Data**.
3. Add the following variables and set them to pull from the URL.

   .. code-block:: text

      Set Embedded Data:

         PROLIFIC_PID   → Value will be set from Panel or URL
         STUDY_ID       → Value will be set from Panel or URL
         SESSION_ID     → Value will be set from Panel or URL

4. Save your Survey Flow.
5. In the ChatbotLab question's JavaScript editor, reference the embedded data:

   .. code-block:: javascript

      Qualtrics.SurveyEngine.addOnload(function() {
         ...
         var prolificParticipantID = "${e://Field/PROLIFIC_PID}";
         var prolificStudyID = "${e://Field/STUDY_ID}";
         var prolificSessionID = "${e://Field/SESSION_ID}";

         botURL += "&participant_id=" + encodeURIComponent(prolificParticipantID);
         botURL += "&prolific_study_id=" + encodeURIComponent(prolificStudyID);
         botURL += "&prolific_session_id=" + encodeURIComponent(prolificSessionID);
      });

Data Storage and Linking
------------------------

When participants complete their chat sessions, Prolific identifiers are saved
in ChatbotLab's backend:

- ``participant_id`` → stored in ``chatbot_conversation.participant_id``
- ``prolific_study_id`` → stored in ``chatbot_conversation.survey_meta_data``
- ``prolific_session_id`` → stored in ``chatbot_conversation.survey_meta_data``

This makes it easy to merge ChatbotLab data with Prolific and survey exports.

Completion Codes
----------------

- Completion codes can be displayed at the end of the chat or survey.
- These codes can also be included in ``survey_meta_data`` for verification.

Best Practices
--------------

- Test your survey link from **Prolific's Preview mode** to confirm that
  ``PROLIFIC_PID``, ``STUDY_ID``, and ``SESSION_ID`` appear in the URL.
- Verify that each conversation appears in ChatbotLab's **Admin Panel** with
  the expected participant ID.
- Keep consistent naming for studies and bots across platforms.
