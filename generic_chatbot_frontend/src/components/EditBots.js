import React, { useState, useEffect } from "react";
import "../styles/EditBots.css";

const BASE_URL = process.env.REACT_APP_API_URL;

function EditBots() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [password, setPassword] = useState("");

  const [bots, setBots] = useState([]);
  const [avatars, setAvatars] = useState([]);

  const [newBot, setNewBot] = useState({
    name: "",
    model_type: "",
    model_id: "",
    prompt: "",
    initial_utterance: "", // ✅ NEW
  });
  const [avatar, setAvatar] = useState({
    bot_name: "",
    avatar_type: "none",
    file: "",
  })

  const [editBotId, setEditBotId] = useState(null);
  const [editForm, setEditForm] = useState({
    name: "",
    model_type: "",
    model_id: "",
    prompt: "",
    initial_utterance: "", // ✅ NEW
  });
  const [editAvatar, setEditAvatar] = useState({
    bot_name: "",
    avatar_type: "none",
    file: "",
  })

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === "humanlikebots12345$") {
      setIsLoggedIn(true);
    } else {
      alert("Invalid password!");
    }
  };

  useEffect(() => {
    if (isLoggedIn) {
      fetchBots();
      fetchAvatars();
    }
  }, [isLoggedIn]);

  const fetchBots = async () => {
    try {
      const response = await fetch(`${BASE_URL}/bots/`);
      const data = await response.json();
      setBots(data.bots || []);
    } catch (error) {
      alert(`Error fetching bots: ${error.message}`);
    }
  };

  const fetchAvatars = async () => {
    try {
      const response = await fetch(`${BASE_URL}/avatar/`);
      const data = await response.json();
      setAvatars(data.avatars || []);
    } catch (error) {
      alert(`Error fetching avatars: ${error.message}`);
    }
  };

  const handleAddBot = async (e) => {
    e.preventDefault();
    try {
      if (avatar.avatar_type==="default" && !avatar.file) return alert("Please select a file first");

      const response = await fetch(`${BASE_URL}/bots/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newBot),
      });
      if (!response.ok) throw new Error(`Failed to create new bot`);

      const formData = new FormData();
      formData.append('bot_name', newBot.name);
      formData.append('avatar_type', avatar.avatar_type);
      formData.append('image', avatar.file);

      fetch(`${BASE_URL}/avatar/`, {
        method: 'POST',
        body: formData,
      });

      setNewBot({
        name: "",
        model_type: "",
        model_id: "",
        prompt: "",
        initial_utterance: "",
      });
      setAvatar({
        bot_name: "",
        avatar_type: "none",
        file: "",
      })
      fetchBots();
      fetchAvatars();
    } catch (error) {
      alert(`Error adding bot: ${error.message}`);
    }
  };

  const handleEditClick = (bot) => {
    setEditBotId(bot.id);
    setEditForm({
      name: bot.name,
      model_type: bot.model_type,
      model_id: bot.model_id,
      prompt: bot.prompt,
      initial_utterance: bot.initial_utterance || "", // ✅ NEW
    });
    setEditAvatar({
      bot_name: bot.name,
      avatar_type: avatars.find(avatar => avatar.bot===bot.id).avatar_type,
    })
  };

  const handleUpdateBot = async (e) => {
    e.preventDefault();
    if (!editBotId) return;
    if (editAvatar.avatar_type==="default" && !editAvatar.file) return alert("Please select a file first");

    try {
      const response = await fetch(`${BASE_URL}/bots/${editBotId}/`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm),
      });
      if (!response.ok) throw new Error(`Failed to update bot`);

      const formData = new FormData();
      formData.append('bot_name', editForm.name);
      formData.append('avatar_type', editAvatar.avatar_type);
      formData.append('image', editAvatar.file);

      fetch(`${BASE_URL}/avatar/${editBotId}/`, {
        method: 'POST',
        body: formData,
      });

      setEditBotId(null);
      setEditForm({
        name: "",
        model_type: "",
        model_id: "",
        prompt: "",
        initial_utterance: "",
      });
      setEditAvatar({
        bot_name: "",
        avatar_type: "none",
        file: "",
      })
      fetchBots();
      fetchAvatars();
    } catch (error) {
      alert(`Error updating bot: ${error.message}`);
    }
  };

  const handleDeleteBot = async (id) => {
    if (!window.confirm("Are you sure you want to delete this bot?")) return;
    try {
      await fetch(`${BASE_URL}/bots/${id}/`, { method: "DELETE" });
      fetchBots();
      fetchAvatars();
    } catch (error) {
      alert(`Error deleting bot: ${error.message}`);
    }
  };

  if (!isLoggedIn) {
    return (
      <div style={{ padding: 20 }}>
        <h2>Researcher Login</h2>
        <form onSubmit={handleLogin}>
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

  return (
    <div className="edit-bots-container">
      <h1>Edit Bots</h1>
      <hr />

      {/* Add New Bot */}
      <h2>Add a New Bot</h2>
      <form onSubmit={handleAddBot}>
        <div>
          <label>Name:</label>
          <input
            type="text"
            value={newBot.name}
            required
            onChange={(e) => setNewBot({ ...newBot, name: e.target.value })}
          />
        </div>
        <div>
          <label>Model Type:</label>
          <input
            type="text"
            value={newBot.model_type}
            required
            onChange={(e) =>
              setNewBot({ ...newBot, model_type: e.target.value })
            }
          />
        </div>
        <div>
          <label>Model ID:</label>
          <input
            type="text"
            value={newBot.model_id}
            required
            onChange={(e) => setNewBot({ ...newBot, model_id: e.target.value })}
          />
        </div>
        <div>
          <label>Prompt:</label>
          <input
            type="text"
            value={newBot.prompt}
            onChange={(e) => setNewBot({ ...newBot, prompt: e.target.value })}
          />
        </div>
        <div>
          <label>Initial Utterance (optional):</label>
          <input
            type="text"
            value={newBot.initial_utterance}
            onChange={(e) =>
              setNewBot({ ...newBot, initial_utterance: e.target.value })
            }
          />
        </div>
        <div>
            <label>Avatar Type: </label>
            <select
              value={avatar.avatar_type}
              onChange={(e) => setAvatar({ ...avatar, avatar_type: e.target.value })}
            >
              <option value="none">None</option>
              <option value="default">Default</option>
              <option value="user">User Provided</option>
            </select>
        </div>
        <div>
            {
            avatar.avatar_type==="default" ?
              <>
                <label>Image:</label>
                <input type="file" accept="image/*" onChange={(e) => setAvatar({ ...avatar, file:e.target.files[0] })} />
              </> :
              <></>
            }
        </div>
        <button type="submit">Add Bot</button>
      </form>

      <hr />

      {/* Bot Table */}
      <h2>Existing Bots</h2>
      {bots.length === 0 ? (
        <p>No bots found.</p>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Model Type</th>
                <th>Model ID</th>
                <th>Prompt</th>
                <th>Initial Utterance</th>
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
                  <td>{bot.initial_utterance}</td>
                  <td>
                    <button onClick={() => handleEditClick(bot)}>Edit</button>
                    <button onClick={() => handleDeleteBot(bot.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit Existing Bot */}
      {editBotId && (
        <div className="edit-form">
          <h2>Edit Bot (ID: {editBotId})</h2>
          <form onSubmit={handleUpdateBot}>
            <div>
              <label>Name:</label>
              <input
                type="text"
                value={editForm.name}
                required
                onChange={(e) =>
                  setEditForm({ ...editForm, name: e.target.value })
                }
              />
            </div>
            <div>
              <label>Model Type:</label>
              <input
                type="text"
                value={editForm.model_type}
                required
                onChange={(e) =>
                  setEditForm({ ...editForm, model_type: e.target.value })
                }
              />
            </div>
            <div>
              <label>Model ID:</label>
              <input
                type="text"
                value={editForm.model_id}
                required
                onChange={(e) =>
                  setEditForm({ ...editForm, model_id: e.target.value })
                }
              />
            </div>
            <div>
              <label>Prompt:</label>
              <input
                type="text"
                value={editForm.prompt}
                onChange={(e) =>
                  setEditForm({ ...editForm, prompt: e.target.value })
                }
              />
            </div>
            <div>
              <label>Initial Utterance (optional):</label>
              <input
                type="text"
                value={editForm.initial_utterance}
                onChange={(e) =>
                  setEditForm({
                    ...editForm,
                    initial_utterance: e.target.value,
                  })
                }
              />
            </div>
            <div>
            <label>Avatar Type: </label>
                <select
                  value={editAvatar.avatar_type}
                  onChange={(e) => setEditAvatar({ ...editAvatar, avatar_type: e.target.value })}
                >
                  <option value="none">None</option>
                  <option value="default">Default</option>
                  <option value="user">User Provided</option>
                </select>
            </div>
            <div>
                {
                editAvatar.avatar_type==="default" ?
                  <>
                    <label>Image:</label>
                    <input type="file" accept="image/*" onChange={(e) => setEditAvatar({ ...editAvatar, file:e.target.files[0] })} />
                  </> :
                  <></>
                }
            </div>
            <button type="submit">Update Bot</button>
          </form>
        </div>
      )}
    </div>
  );
}

export default EditBots;
