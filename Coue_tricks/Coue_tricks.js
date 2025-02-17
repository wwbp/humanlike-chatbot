Qualtrics.SurveyEngine.addOnload(function() {
    var participantID = "${e://Field/ResponseID}";  // Unique qualtrics participant ID
    var studyName = "Coue Tricks";
	var userGroup = "Disclose Chatbot";
    var botName = "Doctor";  // 
    var prompt = "Welcome to the chatbot session!"; // Default initial message


    // Construct chatbot URL with initial prompt as a parameter
    var botURL = "https://bot.wwbp.org/conversation?bot_name=" + botName;
    botURL += "&participant_id=" + encodeURIComponent(participantID);
    botURL += "&study_name=" + encodeURIComponent(studyName);  // Added '=' sign here
    botURL += "&user_group=" + encodeURIComponent(userGroup);   // Added '=' sign here
    botURL += "&prompt=" + encodeURIComponent(prompt);  // Pass initial message

    var container = this.getQuestionTextContainer();  // Correct container

    if (container) {
        var iframe = jQuery("<iframe>", {
            src: botURL,
            width: "100%",
            height:"100vh",
            frameborder: "0"
        });

        jQuery(container).append(iframe);  // Insert iframe
    } else {
        alert("Error: No valid container found.");
    }
});