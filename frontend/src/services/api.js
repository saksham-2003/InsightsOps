import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 120000,
});

// MODIFIED: Now accepts filter parameters to request a specific slice of data
export const getDashboardOverview = async (filters = {}) => {
  const params = new URLSearchParams();
  
  if (filters.year && filters.year !== "All") params.append("year", filters.year);
  if (filters.month && filters.month !== "All") params.append("month", filters.month);
  if (filters.region && filters.region !== "All") params.append("region", filters.region);
  if (filters.category && filters.category !== "All") params.append("category", filters.category);

  const response = await api.get(`/api/analytics/dashboard-overview?${params.toString()}`);
  return response.data;
};

export const queryAIAnalyst = async (question) => {
  const response = await api.post("/api/agent/query", { question });
  return response.data;
};

export const getMonthlyTrend = async () => {
  const response = await api.get("/api/analytics/monthly-trend");
  return response.data;
};

export const getForecastEvaluation = async (filters = {}) => {
  const params = new URLSearchParams();

  if (filters.horizon)
    params.append("horizon", filters.horizon);

  if (filters.region && filters.region !== "All")
    params.append("region", filters.region);

  if (filters.category && filters.category !== "All")
    params.append("category", filters.category);

  if (filters.customDate)
    params.append("customDate", filters.customDate);

  const response = await api.get(
    `/api/ml/forecast-evaluation?${params.toString()}`
  );

  return response.data;
};

export const getAnomalies = async () => {
  const response = await api.get("/api/ml/anomalies");
  return response.data;
};

export default api;