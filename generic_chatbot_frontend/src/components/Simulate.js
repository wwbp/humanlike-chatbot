import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Simulate.css";

const Simulate = () => {
  const [botName, setBotName] = useState("");
  const [participantId, setParticipantId] = useState("");
  const [studyName, setStudyName] = useState("");
  const [initialUtterance, setInitialUtterance] = useState("");
  const [userGroup, setUserGroup] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (event) => {
    event.preventDefault();
  
    if (!botName.trim() || !participantId.trim() || !studyName.trim() || !userGroup.trim()) {
      alert("Please fill in all fields.");
      return;
    }
  
    navigate(
      `/conversation?bot_name=${encodeURIComponent(botName)}&participant_id=${encodeURIComponent(participantId)}&study_name=${encodeURIComponent(studyName)}&user_group=${encodeURIComponent(userGroup)}&initial_utterance=${encodeURIComponent(initialUtterance)}`
    );
  };

  // Navigate to Edit Bots page
  const handleEditBots = () => {
    navigate("/edit-bots");
  };

  return (
    <div className="simulate-container">
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
          <label htmlFor="initialUtterance">Initial Utterance:</label>
          <textarea
            id="initialUtterance"
            value={initialUtterance}
            onChange={(e) => setInitialUtterance(e.target.value)}
            placeholder="Initial utterance(optional)"
          />
        </div>
        <button type="submit" className="btn btn-primary">
          Start Conversation
        </button>
      </form>

      {/* Button to navigate to Edit Bots page */}
      <button onClick={handleEditBots} className="btn btn-secondary" style={{ marginTop: "10px" }}>
        Manage Bots
      </button>
    </div>
  );
};

export default Simulate;
