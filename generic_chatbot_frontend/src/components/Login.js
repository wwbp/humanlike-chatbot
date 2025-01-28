// Login.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Login.css";

const Login = () => {
  const [botName, setBotName] = useState("");
  const [userId, setUserId] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (event) => {
    event.preventDefault();

    if (!botName || !userId) {
      alert("Please fill in both fields.");
      return;
    }

    // Redirect to Conversation page with bot_name and user_id as query parameters
    navigate(`/conversation?bot_name=${botName}&user_id=${userId}`);
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
          <label htmlFor="userId">User ID:</label>
          <input
            type="text"
            id="userId"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Enter user ID"
            required
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