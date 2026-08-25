import Topbar from "../components/topbar";
import KPISection from "../components/KPISection";
import RevenueChart from "../components/RevenueChart";
import CategoryChart from "../components/CategoryChart";
import RegionChart from "../components/RegionChart";
import { formatCurrency } from "../utils/format";

function Dashboard({ dashboardData, loading, error, setActivePage }) {
  const kpis = dashboardData?.kpis;

  return (
    <>
      <Topbar
        title="Business Overview"
        subtitle="Monitor performance and discover AI-powered insights."
        setActivePage={setActivePage}
      />

      {loading && (
        <div className="status-message">Loading business intelligence...</div>
      )}

      {error && <div className="error-message">{error}</div>}

      {!loading && !error && kpis && (
        <>
          <KPISection kpis={kpis} />

          <section className="quick-insights">
            <div>
              <span>Top Category</span>
              <strong>{kpis.top_category}</strong>
            </div>

            <div>
              <span>Top Region</span>
              <strong>{kpis.top_region}</strong>
            </div>

            <div>
              <span>Average Order Value</span>
              <strong>{formatCurrency(kpis.average_order_value)}</strong>
            </div>
          </section>

          <section className="charts-grid">
            <RevenueChart data={dashboardData.monthly_trend} />
            <CategoryChart data={dashboardData.categories} />
            <RegionChart data={dashboardData.regions} />
          </section>
        </>
      )}
    </>
  );
}

export default Dashboard;