import { useEffect, useState } from "react";

import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Forecasting from "./pages/Forecasting";
import Anomalies from "./pages/Anomalies";
import AIAnalyst from "./pages/AIAnalyst";

import { getDashboardOverview } from "./services/api";

import "./App.css";

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activePage, setActivePage] = useState("dashboard");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const response = await getDashboardOverview();
        setDashboardData(response.data);
      } catch (err) {
        console.error(err);
        setError("Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  const renderPage = () => {
    switch (activePage) {
      case "dashboard":
        return (
          <Dashboard
            dashboardData={dashboardData}
            loading={loading}
            error={error}
          />
        );
      case "analytics":
        return <Analytics />;
      case "forecasting":
        return <Forecasting />;
      case "anomalies":
        return <Anomalies />;
      case "ai-analyst":
        return <AIAnalyst />;
      default:
        return null;
    }
  };

  return (
    <div className="app">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      <main className="main-content">{renderPage()}</main>
    </div>
  );
}

export default App;