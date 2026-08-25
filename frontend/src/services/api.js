// src/services/api.js
import axios from "axios";

const api = axios.create({
  baseURL: "https://insightsops-cchb.onrender.com",
  timeout: 120000,
});

export const getDashboardOverview = async (filters = {}) => {
  const params = new URLSearchParams();
  
  if (filters.year && filters.year !== "All") params.append("year", filters.year);
  if (filters.month && filters.month !== "All") params.append("month", filters.month);
  if (filters.region && filters.region !== "All") params.append("region", filters.region);
  if (filters.category && filters.category !== "All") params.append("category", filters.category);

  const response = await api.get(`/api/analytics/dashboard-overview?${params.toString()}`);
  return response.data;
};

// Routes to the full agentic pipeline: Planner → Entity Extraction → Memory →
// Tool Routing → Evidence Analysis → Insight Generator → Recommendation Engine
// → Reflection → Visualization. Previously called /api/ml/ai-analyst (keyword-only).
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

  if (filters.horizon) params.append("horizon", filters.horizon);
  if (filters.region && filters.region !== "All") params.append("region", filters.region);
  if (filters.category && filters.category !== "All") params.append("category", filters.category);
  if (filters.customDate) params.append("customDate", filters.customDate);

  const response = await api.get(`/api/ml/forecast-evaluation?${params.toString()}`);
  return response.data;
};

export const getAnomalies = async (filters = {}) => {
  const params = new URLSearchParams();

  if (filters.region && filters.region !== "All") params.append("region", filters.region);
  if (filters.category && filters.category !== "All") params.append("category", filters.category);
  if (filters.startDate) params.append("startDate", filters.startDate);
  if (filters.endDate) params.append("endDate", filters.endDate);
  if (filters.severity && filters.severity !== "All") params.append("severity", filters.severity);
  if (filters.search) params.append("search", filters.search);

  const response = await api.get(`/api/ml/anomalies?${params.toString()}`);
  return response.data;
};

export default api;