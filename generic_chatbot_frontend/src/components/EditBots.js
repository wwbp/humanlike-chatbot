import React, { useState, useEffect } from "react";

/**
 * A page where only logged-in researchers can:
 * - View a list of bots
 * - Edit existing bots
 * - Delete bots
 * - Add new bots
 */

// (1) Define a BASE URL (adjust for your actual server/port)
const BASE_URL = "http://127.0.0.1:8000";

function EditBots() {
  // -- Auth States --
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // -- Bot-Related States --
  const [bots, setBots] = useState([]);
  const [newBot, setNewBot] = useState({
    name: "",
    model_type: "",
    model_id: "",
    prompt: "",
  });

  // Track editing states
  const [editBotId, setEditBotId] = useState(null);
  const [editForm, setEditForm] = useState({
    name: "",
    model_type: "",
    model_id: "",
    prompt: "",
  });

  // --------------------------------------------
  // 1. Hard-coded login for demonstration
  // --------------------------------------------
  const handleLogin = (e) => {
    e.preventDefault();
    // Hard-coded credential check
    if (username === "admin" && password === "secret123") {
      setIsLoggedIn(true);
    } else {
      alert("Invalid username or password!");
    }
  };

  // --------------------------------------------
  // 2. Fetch bots after "login"
  // --------------------------------------------
  useEffect(() => {
    if (isLoggedIn) {
      fetchBots();
    }
  }, [isLoggedIn]);

  const fetchBots = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/bots/`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch bots. Status: ${response.status}`);
      }
      const data = await response.json(); // { bots: [...] }
      setBots(data.bots || []);
    } catch (error) {
      console.error("fetchBots error:", error);
      alert(`Error fetching bots: ${error.message}`);
    }
  };

  // --------------------------------------------
  // 3. Add a new bot
  // --------------------------------------------
  const handleAddBot = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${BASE_URL}/api/bots/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newBot),
      });
      if (!response.ok) {
        throw new Error(`Failed to create new bot. Status: ${response.status}`);
      }
      // Clear the form and refetch
      setNewBot({ name: "", model_type: "", model_id: "", prompt: "" });
      fetchBots();
    } catch (error) {
      console.error("handleAddBot error:", error);
      alert(`Error adding bot: ${error.message}`);
    }
  };

  // --------------------------------------------
  // 4. Begin editing an existing bot
  // --------------------------------------------
  const handleEditClick = (bot) => {
    setEditBotId(bot.id);
    setEditForm({
      name: bot.name,
      model_type: bot.model_type,
      model_id: bot.model_id,
      prompt: bot.prompt,
    });
  };

  // --------------------------------------------
  // 5. Submit an update to an existing bot
  // --------------------------------------------
  const handleUpdateBot = async (e) => {
    e.preventDefault();
    if (!editBotId) return;

    try {
      const response = await fetch(`${BASE_URL}/api/bots/${editBotId}/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(editForm),
      });
      if (!response.ok) {
        throw new Error(`Failed to update bot. Status: ${response.status}`);
      }
      // Reset state and refetch
      setEditBotId(null);
      setEditForm({ name: "", model_type: "", model_id: "", prompt: "" });
      fetchBots();
    } catch (error) {
      console.error("handleUpdateBot error:", error);
      alert(`Error updating bot: ${error.message}`);
    }
  };

  // --------------------------------------------
  // 6. Delete a bot
  // --------------------------------------------
  const handleDeleteBot = async (id) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this bot?");
    if (!confirmDelete) return;

    try {
      const response = await fetch(`${BASE_URL}/api/bots/${id}/`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`Failed to delete bot. Status: ${response.status}`);
      }
      fetchBots();
    } catch (error) {
      console.error("handleDeleteBot error:", error);
      alert(`Error deleting bot: ${error.message}`);
    }
  };

  // --------------------------------------------
  // Render the login form if not logged in
  // --------------------------------------------
  if (!isLoggedIn) {
    return (
      <div style={{ padding: 20 }}>
        <h2>Researcher Login</h2>
        <form onSubmit={handleLogin}>
          <div>
            <label>Username:</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div>
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit">Login</button>
        </form>
      </div>
    );
  }

  // --------------------------------------------
  // Render the "Edit Bots" interface if logged in
  // --------------------------------------------
  return (
    <div style={{ padding: 20 }}>
      <h1>Edit Bots</h1>
      <hr />

      {/* Add New Bot Form */}
      <h2>Add a New Bot</h2>
      <form onSubmit={handleAddBot}>
        <div>
          <label>Name: </label>
          <input
            type="text"
            value={newBot.name}
            onChange={(e) => setNewBot({ ...newBot, name: e.target.value })}
            required
          />
        </div>
        <div>
          <label>Model Type: </label>
          <input
            type="text"
            value={newBot.model_type}
            onChange={(e) => setNewBot({ ...newBot, model_type: e.target.value })}
            required
          />
        </div>
        <div>
          <label>Model ID: </label>
          <input
            type="text"
            value={newBot.model_id}
            onChange={(e) => setNewBot({ ...newBot, model_id: e.target.value })}
            required
          />
        </div>
        <div>
          <label>Prompt: </label>
          <input
            type="text"
            value={newBot.prompt}
            onChange={(e) => setNewBot({ ...newBot, prompt: e.target.value })}
          />
        </div>
        <button type="submit">Add Bot</button>
      </form>

      <hr />

      {/* List of Existing Bots */}
      <h2>Existing Bots</h2>
      {bots.length === 0 ? (
        <p>No bots found.</p>
      ) : (
        <table border="1" cellPadding="8" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Model Type</th>
              <th>Model ID</th>
              <th>Prompt</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {bots.map((bot) => (
              <tr key={bot.id}>
                <td>{bot.name}</td>
                <td>{bot.model_type}</td>
                <td>{bot.model_id}</td>
                <td>{bot.prompt}</td>
                <td>
                  <button onClick={() => handleEditClick(bot)}>Edit</button>
                  <button onClick={() => handleDeleteBot(bot.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Edit Form */}
      {editBotId && (
        <div style={{ marginTop: 20 }}>
          <h2>Edit Bot (ID: {editBotId})</h2>
          <form onSubmit={handleUpdateBot}>
            <div>
              <label>Name: </label>
              <input
                type="text"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label>Model Type: </label>
              <input
                type="text"
                value={editForm.model_type}
                onChange={(e) => setEditForm({ ...editForm, model_type: e.target.value })}
                required
              />
            </div>
            <div>
              <label>Model ID: </label>
              <input
                type="text"
                value={editForm.model_id}
                onChange={(e) => setEditForm({ ...editForm, model_id: e.target.value })}
                required
              />
            </div>
            <div>
              <label>Prompt: </label>
              <input
                type="text"
                value={editForm.prompt}
                onChange={(e) => setEditForm({ ...editForm, prompt: e.target.value })}
              />
            </div>
            <button type="submit">Update Bot</button>
          </form>
        </div>
      )}
    </div>
  );
}

export default EditBots;
