import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sessionAPI = {
  createSession: async (sessionName = null) => {
    const response = await api.post('/api/session/create', {
      session_name: sessionName,
    });
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await api.get(`/api/session/${sessionId}`);
    return response.data;
  },

  updateEphemeralData: async (sessionId, ephemeralData) => {
    const response = await api.post('/api/session/update-ephemeral', {
      session_id: sessionId,
      ephemeral_data: ephemeralData,
    });
    return response.data;
  },

  deleteSession: async (sessionId) => {
    const response = await api.delete(`/api/session/${sessionId}`);
    return response.data;
  },
};

export const chatAPI = {
  sendMessage: async (sessionId, message, context = null) => {
    const response = await api.post('/api/chat/message', {
      session_id: sessionId,
      message: message,
      context: context,
    });
    return response.data;
  },

  getChatHistory: async (sessionId) => {
    const response = await api.get(`/api/chat/history/${sessionId}`);
    return response.data;
  },
};

export default api;
