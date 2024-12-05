CREATE DATABASE chatbot_db;

USE chatbot_db;

CREATE TABLE utterances (
    conversation_id VARCHAR(255),
    speaker_id VARCHAR(50),
    created_time DATETIME DEFAULT NOW(),
    text TEXT,
    PRIMARY KEY (conversation_id, created_time)
);

CREATE TABLE conversations (
    conversation_id VARCHAR(255) PRIMARY KEY,
    bot_id VARCHAR(50),
    human_id VARCHAR(50),
    started_time DATETIME DEFAULT NOW()
);

CREATE TABLE bot (
    bot_id VARCHAR(50) PRIMARY KEY,
    feature_1 INT DEFAULT 0,
    feature_2 INT DEFAULT 0,
    feature_3 INT DEFAULT 0,
    feature_4 INT DEFAULT 0,
    feature_5 INT DEFAULT 0
);