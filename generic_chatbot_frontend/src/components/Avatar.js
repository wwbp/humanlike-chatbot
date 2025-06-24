import React, { useState, useEffect } from "react";
import "../styles/EditBots.css";

const BASE_URL = process.env.REACT_APP_API_URL;

function Avatar() {
  const [avatar, setAvatar] = useState(null);

  const getAvatar = async () => {
    try {
      const query = new URLSearchParams({
        bot_name: "test_1",
        avatar_type: "default",
      }).toString();
      const response = await fetch(`${BASE_URL}/avatar/?${query}`);
      if (!response.ok) throw new Error(`Failed to get image`);

      const data = await response.json();
      setAvatar(data.image_base64);
    } catch (error) {
      alert(`Error fetching image: ${error.message}`);
    }
  };

  useEffect(() => {
    getAvatar();
  }, []); 

  return (
    <div className="edit-bots-container">
        {avatar ? 
        <img src={avatar} alt="Avatar" className="message-avatar" /> :
        <p>Loading</p>
        }
    </div>
  );
}

export default Avatar;
