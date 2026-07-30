MTurk Integration
=================

Overview
--------

ChatbotLab can integrate directly with **Amazon Mechanical Turk (MTurk)** to link
worker identifiers (Worker IDs, HIT IDs, Assignment IDs) with your survey and
chat conversation data. This enables accurate data merging, auditing, and
protection against data loss.

MTurk metadata is stored automatically in ChatbotLab's backend when passed through
survey URLs.

Workflow Summary
----------------

To use ChatbotLab through MTurk:

1. **Create an MTurk HIT (Human Intelligence Task).**
2. **Set the External Question URL** to your survey (Qualtrics or REDCap)
   that includes a ChatbotLab chatbot.
3. MTurk automatically appends identifying parameters to your survey URL:

   ``?assignmentId=${assignmentId}&workerId=${workerId}&hitId=${hitId}``

4. In your survey, **save each parameter as embedded data**.
5. Pass these values through your ChatbotLab integration code so they are stored
   in the backend database.

   .. code-block:: javascript

      Qualtrics.SurveyEngine.addOnload(function() {
         ...
         var workerID = "<WORKER-ID>";       // MTurk workerId
         var assignmentID = "<ASSIGNMENT-ID>"; // MTurk assignmentId
         var hitID = "<HIT-ID>";               // MTurk hitId

         ...

         botURL += "&participant_id=" + encodeURIComponent(workerID);
         botURL += "&mturk_assignment_id=" + encodeURIComponent(assignmentID);
         botURL += "&mturk_hit_id=" + encodeURIComponent(hitID);
      });

Example (Qualtrics)
-------------------

To capture and link MTurk identifiers in **Qualtrics**:

1. Open your survey.
2. Navigate to **Survey Flow → Add a New Element → Embedded Data**.
3. Add the following variables and set them to pull from the URL:

   .. code-block:: text

      Set Embedded Data:

         workerId     → Value will be set from Panel or URL
         assignmentId → Value will be set from Panel or URL
         hitId        → Value will be set from Panel or URL

4. Save your Survey Flow.
5. In the ChatbotLab question's JavaScript editor, reference the embedded fields:

   .. code-block:: javascript

      Qualtrics.SurveyEngine.addOnload(function() {
         ...
         var workerID = "${e://Field/workerId}";
         var assignmentID = "${e://Field/assignmentId}";
         var hitID = "${e://Field/hitId}";

         ...

         botURL += "&participant_id=" + encodeURIComponent(workerID);
         botURL += "&mturk_assignment_id=" + encodeURIComponent(assignmentID);
         botURL += "&mturk_hit_id=" + encodeURIComponent(hitID);
      });

Data Storage and Linking
------------------------

Once participants complete the chatbot interaction, their MTurk identifiers
are stored within the ChatbotLab database:

- ``participant_id`` → stored in ``chatbot_conversation.participant_id``
- ``mturk_assignment_id`` → stored in ``chatbot_conversation.survey_meta_data``
- ``mturk_hit_id`` → stored in ``chatbot_conversation.survey_meta_data``

These fields can be used to merge ChatbotLab logs with MTurk exports or survey data.

Tracking and Payment Verification
---------------------------------

- You can use the ``assignmentId`` or ``hitId`` values to verify completion
  and automate bonus payments through the MTurk API.
- Completion codes can be displayed on your survey's final page or inside
  the ChatbotLab chat after the final message.
- These codes can also be included in ``survey_meta_data`` for verification.

Best Practices
--------------

- Test your HIT in **MTurk Sandbox** to ensure all parameters
  (`workerId`, `assignmentId`, `hitId`) are properly passed.
- Confirm that conversation entries appear in ChatbotLab's **Admin Panel**
  with matching MTurk metadata.
- Always use the same parameter names (`workerId`, `assignmentId`, `hitId`)
  in both the survey and your ChatbotLab embed script.
