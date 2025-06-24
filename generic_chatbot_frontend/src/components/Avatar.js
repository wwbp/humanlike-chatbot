import React, { useState, useEffect } from "react";
import "../styles/EditBots.css";

function Avatar() {
  const [file, setFile] = useState(null);
  const apiUrl = process.env.REACT_APP_API_URL;

  const handleUpload = async () => {
    if (!file) return alert("Please select a file first");

    const searchParams = new URLSearchParams(window.location.search);
    const botName = searchParams.get("bot_name");
    const botId = searchParams.get("bot_id");
    const conversationId = searchParams.get("conversation_id");
    const participantId = searchParams.get("participant_id");
    console.log("🔧 Params:", { botName, conversationId, participantId });

    const surveyId = searchParams.get("survey_id") || "";
    const studyName = searchParams.get("study_name") || "";
    const userGroup = searchParams.get("user_group") || "";
    const surveyMetaData = window.location.href;

    const formData = new FormData();
      formData.append('bot_name', botName);
      formData.append('conversation_id', conversationId);
      formData.append('image', file);

      fetch(`${apiUrl}/avatar/`, {
        method: 'POST',
        body: formData,
      });

    // const formData = new FormData();
    formData.append('image', file);
    formData.append('bot_name', botName);
    formData.append('conversation_id', conversationId);
    formData.append('participant_id', participantId);
    formData.append('study_name', studyName);
    formData.append('user_group', userGroup);
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
}

export default Avatar;
