// Updated VoiceConversation.js implementing Realtime WebRTC conversation handling per OpenAI docs

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
  const surveyMetaData = window.location.href;

  // Save user or AI utterance
  const saveUtterance = async ({ text, isModel }) => {
    const formData = new FormData();
    formData.append("transcript", text);
    formData.append("conversation_id", conversationId);
    formData.append("participant_id", participantId);
    formData.append("bot_name", botName);
    formData.append("is_model", isModel ? "true" : "false");

    try {
      const res = await fetch(`${apiUrl}/upload_voice_utterance/`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      console.log("✅ Saved utterance:", data);
    } catch (err) {
      console.error("❌ Failed to save utterance:", err);
    }
  };

  useEffect(() => {
    if (!botName || !participantId) return;
    const init = async () => {
      try {
        const res = await fetch(`${apiUrl}/initialize_conversation/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            bot_name: botName,
            conversation_id: conversationId,
            participant_id: participantId,
            survey_meta_data: surveyMetaData,
          }),
        });
        const data = await res.json();
        if (data.initial_utterance) {
          setMessages([{ sender: "AI", content: data.initial_utterance }]);
        }
      } catch (err) {
        console.error("Failed to initialize conversation:", err);
      }
    };
    init();
  }, [botName, participantId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startVoiceConversation = async () => {
    try {
      const sessionRes = await fetch(`${apiUrl}/session/`);
      const { client_secret } = await sessionRes.json();
      const pc = new RTCPeerConnection();
      pcRef.current = pc;

      const audioEl = document.createElement("audio");
      audioEl.autoplay = true;
      document.body.appendChild(audioEl);
      audioRef.current = audioEl;

      pc.ontrack = (e) => {
        audioEl.srcObject = e.streams[0];
      };

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      const dc = pc.createDataChannel("oai-events");
      dcRef.current = dc;

      dc.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log("📨 Message:", message);
        if (message.type === "transcript" && message.final) {
          console.log("📨 Message:", message);
          setMessages((prev) => [...prev, { sender: "You", content: message.text }]);
          saveUtterance({ text: message.text, isModel: false });
          setIsTyping(true);
        }

        if (message.type === "response.content_part.done") {
          console.log("📨 AI Assistant:", message);
          const text = message.part?.transcript
          console.log("Received Message",text);
          saveUtterance({ text: text, isModel: true });
          setIsTyping(false);
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const sdpResponse = await fetch("https://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17", {
        method: "POST",
        body: offer.sdp,
        headers: {
          Authorization: `Bearer ${client_secret.value}`,
          "Content-Type": "application/sdp",
        },
      });

      const answer = { type: "answer", sdp: await sdpResponse.text() };
      await pc.setRemoteDescription(answer);

      setIsConnected(true);
      setIsStreaming(true);
    } catch (err) {
      console.error("❌ Failed to start voice session:", err);
    }
  };

  const stopVoiceConversation = () => {
    if (pcRef.current) pcRef.current.close();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.srcObject = null;
      audioRef.current.remove();
    }
    setIsConnected(false);
    setIsStreaming(false);
  };

  return (
    <div className="conversation-container">
      <div className="chat-box">
        <div className="messages-box">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.sender === "You" ? "sent" : "received"}`}>{msg.content}</div>
          ))}
          {isTyping && (
            <div className="message received typing-indicator">
              <span className="dot"></span><span className="dot"></span><span className="dot"></span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="voice-controls">
          {!isStreaming ? (
            <button className="send-button" onClick={startVoiceConversation}>🎙️ Start Voice Chat</button>
          ) : (
            <button className="send-button stop" onClick={stopVoiceConversation}>⏹️ Stop</button>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceConversation;