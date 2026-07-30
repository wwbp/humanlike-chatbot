Qualtrics Integration
=====================

Overview
--------

Use ChatbotLab to embed conversational tasks into your Qualtrics survey pages.

.. important::

   Note that your Qualtrics account must be able to edit JavaScript. 
   Some institutions disable this for security reasons. Contact your Qualtrics 
   administrator if iframes are not permitted.

Data Needed to Embed Bot
------------------------

ChatbotLab Domain
^^^^^^^^^^^^^^

You must deploy ChatbotLab (following the :doc:`/deployment/index` guide). You will then 
have a domain name for your chatbot, which you put in place of ``<YOUR-CHATLAB-DOMAIN>`` below. 

Survey ID
^^^^^^^^^

1. Navigate to your survey.
2. Click on Distirbutions.
3. Click on **Anonymous link**. If needed you can generate one.
4. Copy the survey ID from the link. It typically starts with ``SV_`` (for example, ``SV_cBaJiOettfQqZRY``).
5. Replace ``<SURVEY-ID>`` with your survey ID in the code below.


Bot Name
^^^^^^^^

1. Navigate to the ChatbotLab admin panel and login. 
2. On the left, under CHATBOT, click on `Bots`.
3. You can use the search bar to find your bot.
4. Copy the name under the NAME column.
5. Replace ``<BOT-NAME>`` with your bot name in the code below.

Alternatively, this could be created in your survey flow and saved to an Embedded Data
field. For example, if your embedded data field was called ``model`` then you would
replace ``<BOT-NAME>`` with ``${e://Field/model}`` in the code below. This allows you
to build sophisticated survey flows and serve different bots depending on how your
participants answer survey questions.

.. important::

   This **must** exactly match the bot name in ChatbotLab's database. 

Study Name
^^^^^^^^^^

This is a descriptive name for your study, which will be saved in ChatbotLab's. For example, 
if you study was related to a therapy bot, you could call the study ``therapy_bot``. We
recommend keeping the name simple, yet descriptive, so that you can distinguish 
between multiple studies. Replace ``<STUDY-NAME>`` with your name in the code below.

Participant ID (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^

You may also have an ID for your participant saved in an Embedded Data field. This
could be a Prolific or Mturk Worker ID. If so, you can replace ``<PARTICIPANT-ID>`` with
your embedded data, for example ``${e://Field/pid}`` if your embedded data field is ``pid``.
If you do not have this then you can set this value as the Response ID ``${e://Field/ResponseID}``,
i.e., a unique identifier for each row in your survey data.

Embedding ChatbotLab
-----------------

1. Deploy ChatbotLab on AWS following the :doc:`/deployment/index` guide.
2. In Qualtrics, add a **Text / Graphic** question.
3. Open the JavaScript editor. This is typically on the left under Edit Question -> Question Behavior
4. Add the following code in the editor under Edit Question JavaScript:

   .. code-block:: javascript

      Qualtrics.SurveyEngine.addOnload(function() {
         var studyName = "<STUDY-NAME>";  
         var botName = "<BOT-NAME>";  // Match expected value
         var surveyID = "<SURVEY-ID>";  //unique survey ID
         var participantID = "<PARTICIPANT-ID>";  // Unique prolific participant ID
         var conversationID = "${e://Field/ResponseID}";  // qualtrics session Id

         window.totalTimeOnPage = 0;
         window.totalTimeAwayFromPage = 0;
         window.pageStartTime = new Date();
         window.awayStartTime = null;

         // Construct chatbot URL with encoded parameters
         var botURL = "https://<YOUR-CHATLAB-DOMAIN>/conversation";
         botURL += "?bot_name=" + encodeURIComponent(botName);
         botURL += "&conversation_id=" + encodeURIComponent(conversationID);
         botURL += "&participant_id=" + encodeURIComponent(participantID);
         botURL += "&study_name=" + encodeURIComponent(studyName);
         botURL += "&user_group=" + encodeURIComponent(userGroup);
         botURL += "&survey_id=" + encodeURIComponent(surveyID);

         console.log("Generated botURL:", botURL);  // Debugging

         var container = this.getQuestionTextContainer();  // Ensure valid container
         if (container) {
            var iframe = jQuery("<iframe>", {
                  src: botURL,
                  width: "100%",
                  height: "100vh",
                  frameborder: "0"
            });
            jQuery(container).append(iframe);  // Insert iframe
         } else {
            alert("Error: No valid container found.");
         }

         function handleVisibilityChange() {
            var currentTime = new Date();
            if (document.hidden) {
                  // User switched to a different tab
                  window.awayStartTime = currentTime;
                  window.totalTimeOnPage += (currentTime - window.pageStartTime);
                  console.log("User is not looking at the page");
            } else {
                  // User returned to the tab
                  if (window.awayStartTime) {
                     window.totalTimeAwayFromPage += (currentTime - window.awayStartTime);
                     window.awayStartTime = null;
                  }
                  window.pageStartTime = currentTime;
                  console.log("User is looking at the page");
            }
         }         

         // Set initial state
         handleVisibilityChange();

         // Listen for visibility change events
         document.addEventListener("visibilitychange", handleVisibilityChange, false);

      });


5. Replace the placeholders:

   - ``<BOT-NAME>`` — your bot's name
   - ``<STUDY-NAME>`` — your chosen study label
   - ``<SURVEY-ID>`` - your unique Qualtrics survey indentifier
   - ``<YOUR-CHATLAB-DOMAIN>`` - 
   - ``<PARTICIPANT-ID>`` (optional)
6. You may also want to add instructions on the task to your **Text / Graphic** question.
7. Save and preview the form to verify that the chat window loads correctly.

Passing Data
------------

You can send other data to ChatbotLab's backend database by adding additional variables and 
appending them to ``botURL``.

   .. code-block:: javascript

         var someSurveyQuestion = "${e://Field/some-question}"; 
         ...
         botURL += "?survey_question_response=" + encodeURIComponent(someSurveyQuestion);

Note that the entirety of ``botURL`` is saved as a raw string in ChatbotLab's backend,
which allows you to send arbitrary amounts of data from your survey without modifying
the database structure (i.e., you can parse variables from the raw string at a later date).

Data Linking
------------

- Each conversation is stored with a ``conversation_id``.
- The variable ``conversation_id`` (in ChatbotLab) can then be merged on the ``ResponseID`` variable in your Qualtrics data.

Keystrokes
----------

You can monitor your participant's typing activity by recording their keystrokes.

   .. code-block:: javascript

      // Function to update time counters and send keystroke data
      function handlePageExit() {
         var currentTime = new Date();
         
         // Ensure we account for time on page before the event
         if (!document.hidden) {
            window.totalTimeOnPage += (currentTime - window.pageStartTime);
         } else if (window.awayStartTime) {
            window.totalTimeAwayFromPage += (currentTime - window.awayStartTime);
         }
         
         sendKeystrokeData();
      }

      // Attach both unload and pagehide events
      Qualtrics.SurveyEngine.addOnUnload(handlePageExit);
      window.addEventListener("pagehide", handlePageExit, false);

      // Function to send keystroke data to external API using both window and sessionStorage flags to avoid duplicate sends
      function sendKeystrokeData() {
         // Check both window and sessionStorage flags
         if (window._keystrokeDataSent || sessionStorage.getItem("keystrokeDataSent") === "true") {
            console.log("Keystroke data already sent.");
            return;
         }
         // Set both flags so that duplicate calls are ignored
         window._keystrokeDataSent = true;
         sessionStorage.setItem("keystrokeDataSent", "true");
         
         var conversationID = "${e://Field/ResponseID}"; // Embedded data from Qualtrics
         var payload = JSON.stringify({
            conversation_id: conversationID,
            total_time_on_page: window.totalTimeOnPage,
            total_time_away_from_page: window.totalTimeAwayFromPage,
            keystroke_count: window.keystrokeCount
         });
         
         if (navigator.sendBeacon) {
            navigator.sendBeacon("https://bot.wwbp.org/api/update_keystrokes/", payload);
            console.log("Keystroke data sent using sendBeacon.");
         } else {
            fetch("https://bot.wwbp.org/api/update_keystrokes/", {  
                  method: "POST",
                  headers: {
                     "Content-Type": "application/json"
                  },
                  body: payload
            })
            .then(response => response.json())
            .then(data => console.log("Keystroke data successfully sent:", data))
            .catch(error => console.error("Error sending keystroke data:", error));
         }
      }


Validation
----------

1. Preview your Qualtrics survey.
2. Open developer console (F12) → check for "Generated botURL" logs.
3. Confirm the embedded ChatbotLab iframe loads successfully.

Other Options
-------------

- You may also want to add a timer question which ensures the participant stays on the chat window for a specified amount of time. 