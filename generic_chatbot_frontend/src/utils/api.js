import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


export async function fetchData(url = "") {
  try {
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error("Error fetching data:", error);
    throw error;
  }
}

export async function postData(url = "", body = {}) {
  try {
    const response = await api.post(url, body);
    return response.data;
  } catch (error) {
    console.error("Error posting data:", error);
    throw error;
  }
}

export async function putData(url = "", body = {}) {
  try {
    const response = await api.put(url, body);
    return response.data;
  } catch (error) {
    console.error("Error putting data:", error);
    throw error;
  }
}

export async function deleteData(url = "") {
  try {
    const response = await api.delete(url);
    return response.data;
  } catch (error) {
    console.error("Error deleting data:", error);
    throw error;
  }
}

export async function createChatSession(moduleId, taskId) {
  try {
    const response = await postData("/chat_sessions/", {
      module: moduleId,
      task: taskId,
    });
    return response;
  } catch (error) {
    console.error("Error creating chat session:", error.message);
    throw error;
  }
}

export async function sendMessage(sessionId, message, sender) {
  try {
    const response = await postData("/chat_messages/", {
      session: sessionId,
      message,
      sender,
    });
    return response;
  } catch (error) {
    console.error("Error sending message:", error.message);
    throw error;
  }
}

export const createWebSocket = (sessionId, isAudioMode) => {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = process.env.REACT_APP_API_URL.replace(
    /^https?/,
    protocol
  ).replace("/api/v1", "");
  const endpoint = isAudioMode
    ? `/ws/audio/${sessionId}/`
    : `/ws/chat/${sessionId}/`;
  return new WebSocket(`${wsUrl}${endpoint}`);
};

export const postFile = async (filePath, formData) => {
  try {
    const response = await api.post(filePath, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error posting file:", error);
    throw error;
  }
};

export async function fetchFile(url = "") {
  try {
    const response = await api.get(url, { responseType: "blob" });
    return response.data;
  } catch (error) {
    console.error("Error fetching file:", error);
    throw error;
  }
}

export async function getPresignedUrl(fileName, fileType, isAvatar = false) {
  try {
    const urlPath = isAvatar ? "/get-avatar-url/" : "/generate_presigned_url/";
    const response = await api.post(urlPath, {
      file_name: fileName,
      file_type: fileType,
      is_avatar: isAvatar,
    });
    return response.data;
  } catch (error) {
    console.error("Error getting presigned URL:", error);
    throw error;
  }
}

export async function getPresignedUrlForDisplay(fileName) {
  try {
    const response = await api.get(
      `/generate_presigned_url/?file_name=${encodeURIComponent(fileName)}`
    );
    console.log("Response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error getting presigned URL:", error);
    throw error;
  }
}

export async function getLocalFile(fileName) {
  try {
    console.log("Getting local file:", fileName);
    const response = await api.get(`/local_upload/?file_name=${fileName}`, {
      responseType: "blob", // Treat the response as a Blob
    });
    return response.data;
  } catch (error) {
    console.error("Error getting local file:", error);
    throw error;
  }
}

export async function uploadToS3(url, fields, file) {
  const formData = new FormData();
  Object.entries({ ...fields, file }).forEach(([key, value]) => {
    formData.append(key, value);
  });

  await axios.post(url, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

export default api;
