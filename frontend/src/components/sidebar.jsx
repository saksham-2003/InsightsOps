import {
  LayoutDashboard,
  ChartNoAxesCombined,
  TrendingUp,
  TriangleAlert,
  BrainCircuit,
} from "lucide-react";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "analytics", label: "Analytics", icon: ChartNoAxesCombined },
  { id: "forecasting", label: "Forecasting", icon: TrendingUp },
  { id: "anomalies", label: "Anomalies", icon: TriangleAlert },
  { id: "ai-analyst", label: "AI Analyst", icon: BrainCircuit },
];

function Sidebar({ activePage, setActivePage }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">IO</div>

        <div>
          <h2>InsightsOps</h2>
          <p>Decision Intelligence</p>
        </div>
      </div>

      <nav className="nav-menu">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item ${activePage === id ? "active" : ""}`}
            onClick={() => setActivePage(id)}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;