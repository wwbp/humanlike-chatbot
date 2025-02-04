import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Login.css";

const Login = () => {
  const [botName, setBotName] = useState("");
  const [participantId, setParticipantId] = useState("");
  const [studyName, setStudyName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [userGroup, setUserGroup] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (event) => {
    event.preventDefault();

    if (!botName || !participantId || !studyName || !userGroup) {
      alert("Please fill in all fields.");
      return;
    }

    // Redirect to Conversation page with parameters
    navigate(
      `/conversation?bot_name=${encodeURIComponent(botName)}&participant_id=${encodeURIComponent(participantId)}&study_name=${encodeURIComponent(studyName)}&user_group=${encodeURIComponent(userGroup)}&prompt=${encodeURIComponent(prompt)}`
    );
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="botName">Bot Name:</label>
          <input
            type="text"
            id="botName"
            value={botName}
            onChange={(e) => setBotName(e.target.value)}
            placeholder="Enter bot name"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="participantId">Participant ID:</label>
          <input
            type="text"
            id="participantId"
            value={participantId}
            onChange={(e) => setParticipantId(e.target.value)}
            placeholder="Enter participant ID"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="studyName">Study Name:</label>
          <input
            type="text"
            id="studyName"
            value={studyName}
            onChange={(e) => setStudyName(e.target.value)}
            placeholder="Enter study name"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="userGroup">User Group:</label>
          <input
            type="text"
            id="userGroup"
            value={userGroup}
            onChange={(e) => setUserGroup(e.target.value)}
            placeholder="Enter user group"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="prompt">Prompt:</label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter prompt (optional)"
          />
        </div>
        <button type="submit" className="btn btn-primary">
          Start Conversation
        </button>
      </form>
    </div>
  );
};

export default Login;
