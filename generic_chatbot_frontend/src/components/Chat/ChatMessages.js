import React from "react";

const ChatMessages = ({ messages }) => {
    return (
        <div className="chat-messages">
            {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.sender}`}>
                    <b>{msg.sender === "user" ? "You" : "Bot"}</b>: {msg.text}
                </div>
            ))}
        </div>
    );
};

export default ChatMessages;
