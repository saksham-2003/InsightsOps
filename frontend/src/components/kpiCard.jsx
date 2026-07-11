function KpiCard({ title, value, subtitle, icon }) {
  return (
    <article className="kpi-card">
      <div className="kpi-card-header">
        <span className="kpi-title">{title}</span>
        <div className="kpi-icon">{icon}</div>
      </div>

      <h2 className="kpi-value">{value}</h2>

      <p className="kpi-subtitle">{subtitle}</p>
    </article>
  );
}

export default KpiCard;