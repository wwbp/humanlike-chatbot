Qualtrics.SurveyEngine.addOnload(function() {
    var participantID = "${e://Field/ResponseID}";  // Unique qualtrics participant ID
    var condition = "${e://Field/CONDITION}";  // Assigned group

    // Set chatbot type and initial prompt based on participant's assigned condition
    var botName = "DefaultBot";  // Fallback bot
    var initialPrompt = "Welcome to the chatbot session!"; // Default initial message

    if (condition === "Disclose_Chatbot") {
        botName = "Doctor";
        initialPrompt = "Hello! I am a chatbot here to assist you.";
    } else if (condition === "NoDisclose_Chatbot") {
        botName = "Doctor";
        initialPrompt = "Hi! Let's have a conversation.";
    } else if (condition === "Disclose_Human") {
        botName = "Assistant";
        initialPrompt = "Hello! I am a real human here to talk with you.";
    } else if (condition === "NoDisclose_Human") {
        botName = "Assistant";
        initialPrompt = "Hi! Let's chat.";
    }

    // Construct chatbot URL with initial prompt as a parameter
    var botURL = "https://bot.wwbp.org/conversation?bot_name=" + botName;
    botURL += "&user_id=" + encodeURIComponent(participantID);
    botURL += "&prompt=" + encodeURIComponent(initialPrompt);  // Pass initial message

    var container = this.getQuestionTextContainer();  // Correct container

    if (container) {

        var iframe = jQuery("<iframe>", {
            src: botURL,
            width: "100%",
            frameborder: "0"
        });

        jQuery(container).append(iframe);  // Insert iframe
    } else {
        alert("Error: No valid container found.");
    }
});