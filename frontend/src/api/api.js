import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10s timeout
});

// Attach the JWT (if present) to every outgoing request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sif_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for centralized error logging and observability
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const timestamp = new Date().toISOString();
    const endpoint = error.config ? `${error.config.method?.toUpperCase()} ${error.config.url}` : 'UNKNOWN_URL';
    const status = error.response ? error.response.status : 'NETWORK_OR_TIMEOUT';
    const data = error.response ? error.response.data : error.message;

    console.error(
      `[SentinelSIF API ERROR] ${timestamp} | Endpoint: ${endpoint} | Status: ${status}`,
      data
    );

    // A 401 means the token is invalid/expired — clear it so the next
    // protected-route check redirects to /login instead of looping.
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('sif_token');
    }

    return Promise.reject(error);
  }
);

export default api;