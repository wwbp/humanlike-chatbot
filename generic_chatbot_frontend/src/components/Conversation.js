import React, { useState, useEffect, useRef } from "react";

const Conversation = () => {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  const apiUrl = "http://0.0.0.0:8000/api";

  // Extract query parameters
  const searchParams = new URLSearchParams(window.location.search);
  const botName = searchParams.get("bot_name");
  const userId = searchParams.get("user_id");

  const [isInitialized, setIsInitialized] = useState(false);

useEffect(() => {
  const initializeConversation = async () => {
    if (!botName || !userId || isInitialized) {
      console.error("Missing botName, userId, or conversation already initialized.");
      return;
    }

    try {
      console.log("Initializing conversation with:", { botName, userId });

      const response = await fetch(`${apiUrl}/initialize_conversation/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          bot_name: botName,
          user_id: userId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Failed to initialize conversation:", errorData);
        throw new Error(errorData.error || "Failed to initialize conversation");
      }

      const data = await response.json();
      setConversationId(data.conversation_id);
      console.log("Conversation initialized:", data.conversation_id);

      // Mark as initialized
      setIsInitialized(true);
    } catch (error) {
      console.error("Error initializing conversation:", error);
    }
  };

  if (botName && userId) {
    initializeConversation();
  } else {
    console.error("botName or userId missing.");
  }
}, [apiUrl, botName, userId, isInitialized]);


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (event) => {
    event.preventDefault();

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
        body: JSON.stringify({
          message,
          bot_name: botName,
          user_id: userId,
          conversation_id: conversationId, // Use existing conversation_id
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        alert(`Error: ${errorData.error || "Something went wrong"}`);
        return;
      }

      const data = await response.json();

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
    <div className="conversation-container">
      <h1>Chat with {botName}</h1>
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
};

export default Conversation;
