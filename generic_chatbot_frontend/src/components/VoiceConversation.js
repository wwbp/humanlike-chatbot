import React, { useState, useEffect, useRef } from "react";
import "../styles/Conversation.css";

const VoiceConversation = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const pcRef = useRef(null);
  const dcRef = useRef(null);
  const audioRef = useRef(null);
  const messagesEndRef = useRef(null);

  const apiUrl = process.env.REACT_APP_API_URL;

  const searchParams = new URLSearchParams(window.location.search);
  const botName = searchParams.get("bot_name");
  const conversationId = searchParams.get("conversation_id");
  const participantId = searchParams.get("participant_id");

  const surveyId = searchParams.get("survey_id") || "";
  const studyName = searchParams.get("study_name") || "";
  const userGroup = searchParams.get("user_group") || "";
  const surveyMetaData = window.location.href;

  useEffect(() => {
    if (!botName || !participantId) {
      console.warn("Missing botName or participantId");
      return;
    }

    const initializeConversation = async () => {
      try {
        const response = await fetch(`${apiUrl}/initialize_conversation/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            bot_name: botName,
            conversation_id: conversationId,
            participant_id: participantId,
            study_name: studyName,
            user_group: userGroup,
            survey_id: surveyId,
            survey_meta_data: surveyMetaData,
          }),
        });

        const data = await response.json();
        if (data.initial_utterance?.trim()) {
          setMessages([{ sender: "AI", content: data.initial_utterance }]);
        }
      } catch (error) {
        console.error("Failed to initialize conversation:", error);
      }
    };

    initializeConversation();
  }, [apiUrl, botName, participantId, conversationId, studyName, surveyId, surveyMetaData, userGroup]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startVoiceConversation = async () => {
    try {
      const sessionRes = await fetch(`${apiUrl}/session/`);
      const sessionData = await sessionRes.json();
      const EPHEMERAL_KEY = sessionData.client_secret.value;

      const pc = new RTCPeerConnection();
      pcRef.current = pc;

      const audioEl = document.createElement("audio");
      audioEl.autoplay = true;
      document.body.appendChild(audioEl);
      audioRef.current = audioEl;

      pc.ontrack = (e) => {
        audioEl.srcObject = e.streams[0];
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      pc.addTrack(mediaStream.getTracks()[0]);

      const dc = pc.createDataChannel("oai-events");
      dcRef.current = dc;

      dc.onmessage = (e) => {
        try {
          const message = JSON.parse(e.data);
          console.log("📨 Message from model:", message);

          if (message.type === "message" && message.text) {
            setMessages((prev) => [...prev, { sender: "AI", content: message.text }]);
            setIsTyping(false);
          }

          if (message.type === "transcript" && message.final) {
            setMessages((prev) => [...prev, { sender: "You", content: message.text }]);
            setIsTyping(true);
          }
        } catch (err) {
          console.error("Failed to parse message:", err);
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const sdpResponse = await fetch(
        `https://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17`,
        {
          method: "POST",
          body: offer.sdp,
          headers: {
            Authorization: `Bearer ${EPHEMERAL_KEY}`,
            "Content-Type": "application/sdp",
          },
        }
      );

      const answer = {
        type: "answer",
        sdp: await sdpResponse.text(),
      };
      await pc.setRemoteDescription(answer);

      setIsConnected(true);
      setIsStreaming(true);
    } catch (error) {
      console.error("❌ Failed to start voice conversation:", error);
      alert("Could not start voice conversation. Check console.");
    }
  };

  const stopVoiceConversation = () => {
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.srcObject = null;
      audioRef.current.remove();
    }
    setIsStreaming(false);
    setIsConnected(false);
  };

  return (
    <div className="conversation-container">
      <div className="chat-box">
        <div className="messages-box">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.sender === "You" ? "sent" : "received"}`}
            >
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
          <div ref={messagesEndRef} />
        </div>

        <div className="voice-controls">
          {!isStreaming ? (
            <button className="send-button" onClick={startVoiceConversation}>
              🎙️ Start Voice Chat
            </button>
          ) : (
            <button className="send-button stop" onClick={stopVoiceConversation}>
              ⏹️ Stop
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceConversation;

