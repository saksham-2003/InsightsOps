import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 120000,
});

export const getDashboardOverview = async () => {
  const response = await api.get("/api/analytics/dashboard-overview");

  return response.data;
};

export default api;