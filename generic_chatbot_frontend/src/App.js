import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [botName, setBotName] = useState("");
  const [bots, setBots] = useState([]);
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);

  const apiUrl = 'http://0.0.0.0:8000/api';

  // Fetch bots list from the backend
  useEffect(() => {
    const fetchBots = async () => {
      try {
        const response = await fetch(`${apiUrl}/bots/`);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Bots fetched:", data.bot_names);
        setBots(data.bot_names || []);
      } catch (error) {
        console.error("Error fetching bots:", error);
      }
    };
    fetchBots();
  }, []);

  // Scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


  const handleSubmit = async (event) => {
    event.preventDefault();
  
    if (!botName) {
      alert("Please select a bot.");
      return;
    }
  
    if (message.trim() === "") {
      alert("Please enter a message.");
      return;
    }
  
    setMessages((prevMessages) => [
      ...prevMessages,
      { sender: "You", content: message },
    ]);
  
    try {
      const response = await fetch(`${apiUrl}/chatbot/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message, bot_name: botName }),
      });
  
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Error: ${errorData.error || "Something went wrong"}`);
        return;
      }
  
      const data = await response.json();
      console.log("Chatbot response:", data);
  
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "AI Chatbot", content: data.response },
      ]);
    } catch (error) {
      console.error("Error sending message:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setMessage("");
    }
  };
  

  return (
    <div className="chat-container">
      <div className="card flex-grow-1">
        <div className="card-body messages-box">
          <ul className="list-unstyled messages-list">
            {messages.map((msg, index) => (
              <li
                key={index}
                className={`message ${
                  msg.sender === "You" ? "sent" : "received"
                }`}
              >
                <div className="message-text">
                  <div className="message-sender">
                    <b>{msg.sender}</b>
                  </div>
                  <div className="message-content">{msg.content}</div>
                </div>
              </li>
            ))}
            <div ref={messagesEndRef}></div>
          </ul>
        </div>
      </div>

      <form className="message-form" onSubmit={handleSubmit}>
        <div className="bot-selector-container">
          <label htmlFor="bot-selector" className="form-label">
            Choose a bot:
          </label>
          <select
            id="bot-selector"
            className="form-select bot-selector"
            value={botName}
            onChange={(e) => setBotName(e.target.value)}
            required
          >
            <option value="" disabled>
              -- Select a bot --
            </option>
            {bots.map((bot, index) => (
              <option key={index} value={bot}>
                {bot}
              </option>
            ))}
          </select>
        </div>

        <div className="input-group">
          <input
            type="text"
            className="form-control message-input"
            placeholder="Type your message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            required
          />
          <div className="input-group-append">
            <button type="submit" className="btn btn-primary btn-send">
              Send
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default App;
