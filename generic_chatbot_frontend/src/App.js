import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./components/Login";
import Conversation from "./components/Conversation";
import EditBots from "./components/EditBots";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/conversation" element={<Conversation />} />
        <Route path="/edit-bots" element={<EditBots />} />
      </Routes>
    </Router>
  );
}

export default App;
