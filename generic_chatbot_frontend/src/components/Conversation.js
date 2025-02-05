import React, { useState, useEffect, useRef } from "react";
import "../styles/Conversation.css";

const Conversation = () => {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  /*const apiUrl = "http://0.0.0.0:8000/api";*/
  const apiUrl = "https://bot.wwbp.org/api";

  const searchParams = new URLSearchParams(window.location.search);
  const botName = searchParams.get("bot_name");
  const participantId = searchParams.get("participant_id");
  const prompt = searchParams.get("prompt") || "";
  const studyName = searchParams.get("study_name") || "Default study name";
  const userGroup = searchParams.get("user_group") || "na";

  useEffect(() => {
    if (prompt && prompt.trim() !== "") {
      setMessages([{ sender: "bot", content: prompt }]);
    }
  }, [prompt]);
  
  useEffect(() => {
    const initializeConversation = async () => {
      if (!botName || !participantId) {
        return;
      }
      try {
        const response = await fetch(`${apiUrl}/initialize_conversation/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ bot_name: botName, participant_id: participantId,prompt:prompt,study_name: studyName, user_group:userGroup}),
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to initialize conversation");
        }
        const data = await response.json();
        setConversationId(data.conversation_id);
      } catch (error) {
        console.error("Error initializing conversation:", error);
      }
    };
    initializeConversation();
  }, [apiUrl, botName, participantId, conversationId,prompt,studyName,userGroup]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (message.trim() === "") {
      alert("Please enter a message.");
      return;
    }
    setMessages((prevMessages) => [...prevMessages, { sender: "You", content: message }]);
    setMessage("");
    setIsTyping(true);

    try {
      const response = await fetch(`${apiUrl}/chatbot/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          bot_name: botName,
          participant_id: participantId,
          conversation_id: conversationId,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Error: ${errorData.error || "Something went wrong"}`);
        return;
      }
      const data = await response.json();
      setTimeout(() => {
        setMessages((prevMessages) => [...prevMessages, { sender: "AI Chatbot", content: data.response }]);
        setIsTyping(false);
      }, 1500); // Simulating chatbot "thinking" time
    } catch (error) {
      console.error("Error sending message:", error);
      alert("An error occurred. Please try again.");
      setIsTyping(false);
    }
  };

  return (
    <div className="conversation-container">
      <div className="chat-box">
        <div className="messages-box">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender === "You" ? "sent" : "received"}`}>
              {msg.content}
            </div>
          ))}
          {isTyping && (
            <div className="message received typing-indicator">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          )}
          <div ref={messagesEndRef}></div>
        </div>
        <form className="message-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="message-input"
            placeholder="Type your message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            required
          />
          <button type="submit" className="send-button">Send</button>
        </form>
      </div>
    </div>
  );
};

export default Conversation;