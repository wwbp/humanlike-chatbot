import React, { useState, useEffect, useRef } from "react";
import "../styles/Conversation.css";

const Conversation = () => {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const apiUrl = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000/api";


  const searchParams = new URLSearchParams(window.location.search);
  const botName = searchParams.get("bot_name");
  const participantId = searchParams.get("participant_id");
  const initialUtterance = searchParams.get("initial_utterance") || "";
  const surveyId = searchParams.get("survey_id") || "";
  const studyName = searchParams.get("study_name") || "";
  const userGroup = searchParams.get("user_group") || "";
  const surveyMetaData = window.location.href;

  useEffect(() => {
    if (initialUtterance.trim() !== "") {
      setMessages([{ sender: "bot", content: initialUtterance }]);
    }
  }, [initialUtterance]);

  useEffect(() => {
    if (!botName || !participantId) {
      console.log("Cannot initialize conversation with botname or participantId");
      return;
    }
  
    // Prevent re-initialization if conversation already exists
    if (conversationId) {
      console.log("Conversation already initialized.");
      return;
    }
  
    const initializeConversation = async () => {
      try {
        console.log("🚀 Initializing conversation...");
        const response = await fetch(`${apiUrl}/initialize_conversation/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            bot_name: botName,
            participant_id: participantId,
            initial_utterance: initialUtterance,
            study_name: studyName,
            user_group: userGroup,
            survey_id: surveyId,
            survey_meta_data: surveyMetaData,
          }),
        });
  
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to initialize conversation");
        }
  
        const data = await response.json();
        console.log("✅ Conversation Initialized:", data.conversation_id);
        setConversationId(data.conversation_id);
      } catch (error) {
        console.error("❌ Error initializing conversation:", error);
      }
    };
  
    initializeConversation();
  }, [botName, participantId, initialUtterance, studyName, surveyId, surveyMetaData, userGroup, conversationId]);
  
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
      console.log(`📤 Sending message: ${message}`);
      const response = await fetch(`${apiUrl}/chatbot/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
        setIsTyping(false);
        return;
      }

      const data = await response.json();
      setTimeout(() => {
        setMessages((prevMessages) => [
          ...prevMessages,
          { sender: "AI Chatbot", content: data.response },
        ]);
        setIsTyping(false);
      }, 500);
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
            // Prevent paste, copy, and cut
            onPaste={(e) => {
              e.preventDefault();
              alert("You can't paste here!");
            }}
            onCopy={(e) => e.preventDefault()}
            onCut={(e) => e.preventDefault()}
            // (Optional) Prevent right-click context menu
            onContextMenu={(e) => e.preventDefault()}
          />
          <button type="submit" className="send-button">Send</button>
        </form>
      </div>
    </div>
  );
};

export default Conversation;