import React, { useState, useEffect, useRef } from "react";
import "../styles/VoiceConversation.css";

const VoiceConversation = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const pcRef = useRef(null);
  const dcRef = useRef(null);
  const audioRef = useRef(null);
  const userRecorderRef = useRef(null);
  const userChunksRef = useRef([]);
  const assistantRecorderRef = useRef(null);
  const assistantChunksRef = useRef([]);
  const assistantStreamRef = useRef(null);
  const assistantTranscriptRef = useRef("");

  const apiUrl = process.env.REACT_APP_API_URL;
  const searchParams = new URLSearchParams(window.location.search);
  const botName = searchParams.get("bot_name");
  const conversationId = searchParams.get("conversation_id");
  const participantId = searchParams.get("participant_id");
  const surveyId = searchParams.get("survey_id") || "";
  const studyName = searchParams.get("study_name") || "";
  const userGroup = searchParams.get("user_group") || "";
  const surveyMetaData = window.location.href;

  const saveUtterance = async ({ text, audioFile = null, isAssistant = false }) => {
    const formData = new FormData();
    formData.append("transcript", text);
    formData.append("conversation_id", conversationId);
    formData.append("is_voice", "true");

    if (audioFile) formData.append("audio", audioFile);
    if (isAssistant) formData.append("bot_name", botName);
    else formData.append("participant_id", participantId);

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
        await fetch(`${apiUrl}/initialize_conversation/`, {
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
        console.log("✅ Conversation initialized");
      } catch (err) {
        console.error("Failed to initialize conversation:", err);
      }
    };

    init();
  }, [botName, participantId]);

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
        const assistantStream = e.streams[0];
        audioEl.srcObject = assistantStream;
        assistantStreamRef.current = assistantStream;
      };

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      const startUserRecorder = () => {
        userChunksRef.current = [];
        const recorder = new MediaRecorder(stream);
        userRecorderRef.current = recorder;

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) userChunksRef.current.push(e.data);
        };

        recorder.start();
      };

      startUserRecorder();

      const dc = pc.createDataChannel("oai-events");
      dcRef.current = dc;

      let assistantBuffer = "";

      dc.onopen = () => {
        dc.send(
          JSON.stringify({
            type: "session.update",
            session: {
              input_audio_transcription: {
                model: "whisper-1",
              },
            },
          })
        );
        console.log("📡 Sent session.update to enable user speech transcription");
      };

      dc.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log("📨 Message:", message);

        if (message.type === "conversation.item.input_audio_transcription.completed") {
          const transcript = message.transcript?.trim();
          if (transcript && userRecorderRef.current) {
            userRecorderRef.current.onstop = async () => {
              const blob = new Blob(userChunksRef.current, { type: "audio/webm" });
              const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
              const uniqueId = `${participantId || "user"}_${conversationId || "conv"}_${timestamp}`;
              const audioFile = new File([blob], `${uniqueId}.webm`, { type: "audio/webm" });

              await saveUtterance({ text: transcript, audioFile });
              setIsTyping(true);
              startUserRecorder();
            };

            userRecorderRef.current.stop();
          }
        }

        if (message.type === "response.content_part") {
          const partial = message.part?.transcript;
          if (partial) assistantBuffer += partial + " ";
        }

        if (message.type === "response.content_part.begin") {
          if (assistantStreamRef.current) {
            assistantChunksRef.current = [];
            const recorder = new MediaRecorder(assistantStreamRef.current);
            assistantRecorderRef.current = recorder;

            recorder.ondataavailable = (e) => {
              if (e.data.size > 0) assistantChunksRef.current.push(e.data);
            };

            recorder.start();
          }
        }

        if (message.type === "response.content_part.done") {
          const finalText = message.part?.transcript?.trim();
          if (finalText) {
            assistantTranscriptRef.current = finalText;
          }

          const trySaveAssistantUtterance = async () => {
            const text = assistantTranscriptRef.current;
            const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
            const uniqueId = `assistant_${conversationId || "conv"}_${timestamp}`;

            if (assistantChunksRef.current.length > 0) {
              const blob = new Blob(assistantChunksRef.current, { type: "audio/webm" });
              const audioFile = new File([blob], `${uniqueId}.webm`, { type: "audio/webm" });

              await saveUtterance({ text, audioFile, isAssistant: true });
            } else {
              await saveUtterance({ text, isAssistant: true });
            }
          };

          if (
            assistantRecorderRef.current &&
            assistantRecorderRef.current.state !== "inactive"
          ) {
            assistantRecorderRef.current.onstop = trySaveAssistantUtterance;
            assistantRecorderRef.current.stop();
          } else {
            trySaveAssistantUtterance();
          }

          assistantBuffer = "";
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

    if (userRecorderRef.current && userRecorderRef.current.state !== "inactive") {
      userRecorderRef.current.stop();
    }

    if (assistantRecorderRef.current && assistantRecorderRef.current.state !== "inactive") {
      assistantRecorderRef.current.stop();
    }

    setIsConnected(false);
    setIsStreaming(false);
  };

  return (
    <div className="voice-conversation">
      <div className="conversation-container">
        <div className="chat-box">
          <div className="voice-status">
            {isStreaming ? (
              <p className="status-text">🎤 Listening...</p>
            ) : (
              <p className="status-text">Press the button to start talking</p>
            )}
            {isTyping && (
              <div className="typing-indicator">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            )}
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
    </div>
  );
};

export default VoiceConversation;


