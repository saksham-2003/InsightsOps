import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import {
  Siren,
  AlertTriangle,
  Layers,
  Percent,
  ListTree,
  ShieldAlert,
  Lightbulb,
  HeartPulse,
} from "lucide-react";

import { formatCurrency, formatNumber } from "../utils/format";
import { getAnomalies } from "../services/api";

// Warning-family palette — deliberately distinct from the indigo/violet
// identity used on Dashboard, Analytics, and Forecasting.
const COLORS = {
  red: "#dc2626",
  redBg: "#fef2f2",
  orange: "#ea580c",
  orangeBg: "#fff7ed",
  yellow: "#ca8a04",
  yellowBg: "#fefce8",
  green: "#15803d",
  greenBg: "#f0fdf4",
  ink: "#1c1917",
  subtext: "#78716c",
  border: "#e7e0d9",
  panelBg: "#fffdfb",
};

const RISK_META = {
  High: {
    color: COLORS.red,
    bg: COLORS.redBg,
    health: "Needs Attention",
    note: "Anomaly scores indicate high-severity outliers. Prioritize manual review.",
  },
  Medium: {
    color: COLORS.orange,
    bg: COLORS.orangeBg,
    health: "Monitor Closely",
    note: "Anomaly scores are moderately elevated. Periodic review is recommended.",
  },
  Low: {
    color: COLORS.yellow,
    bg: COLORS.yellowBg,
    health: "Healthy",
    note: "Anomaly scores are relatively mild across flagged transactions.",
  },
};

// Ranks each anomaly's severity relative to the others in this dataset.
// Assumes a HIGHER Anomaly_Score means MORE anomalous — flip the comparison
// below if your model uses the opposite convention.
const buildSeverityRanker = (scores) => {
  const max = scores.length ? Math.max(...scores) : 0;
  const min = scores.length ? Math.min(...scores) : 0;
  const range = max - min || 1;

  return (score) => {
    const normalized = (score - min) / range;
    if (normalized >= 0.66) return "High";
    if (normalized >= 0.33) return "Medium";
    return "Low";
  };
};

function Anomalies() {
  const [anomalyData, setAnomalyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadAnomalies = async () => {
      try {
        const response = await getAnomalies();
        setAnomalyData(response.data);
      } catch (err) {
        console.error(err);
        setError("Unable to load anomaly data.");
      } finally {
        setLoading(false);
      }
    };

    loadAnomalies();
  }, []);

  const summary = anomalyData?.summary;
  const allAnomalies = anomalyData?.top_anomalies ?? [];
  const top10 = allAnomalies.slice(0, 10);

  const featuresUsed = summary?.features_used;
  const featuresCount = Array.isArray(featuresUsed)
    ? featuresUsed.length
    : featuresUsed ?? 0;
  const featuresList = Array.isArray(featuresUsed)
    ? featuresUsed.join(", ")
    : null;

  const scores = allAnomalies.map((row) => row.Anomaly_Score);
  const getSeverity = buildSeverityRanker(scores);

  const averageScore = scores.length
    ? scores.reduce((sum, s) => sum + s, 0) / scores.length
    : 0;
  const overallRisk = scores.length ? getSeverity(averageScore) : "Low";
  const risk = RISK_META[overallRisk];

  const highestRevenueAnomaly = allAnomalies.reduce(
    (max, row) => (!max || row.Revenue > max.Revenue ? row : max),
    null
  );

  const highestProfitAnomaly = allAnomalies.reduce(
    (max, row) => (!max || row.Profit > max.Profit ? row : max),
    null
  );

  const productCounts = allAnomalies.reduce((acc, row) => {
    acc[row.Product_Name] = (acc[row.Product_Name] || 0) + 1;
    return acc;
  }, {});

  const mostCommonProductEntry = Object.entries(productCounts).sort(
    (a, b) => b[1] - a[1]
  )[0];

  const repeatedProducts = Object.entries(productCounts).filter(
    ([, count]) => count > 1
  );

  const scatterData = allAnomalies.map((row) => ({
    revenue: row.Revenue,
    profit: row.Profit,
    score: row.Anomaly_Score,
    product: row.Product_Name,
    orderId: row.Order_ID,
  }));

  const businessReasons = [];

  if (summary && allAnomalies.length > 0) {
    businessReasons.push(
      `Overall anomaly risk is ${overallRisk.toLowerCase()} based on an average anomaly score of ${averageScore.toFixed(
        3
      )} across ${allAnomalies.length} flagged transactions.`
    );

    if (mostCommonProductEntry) {
      businessReasons.push(
        `"${mostCommonProductEntry[0]}" recurs ${mostCommonProductEntry[1]} times among flagged transactions — this may point to a pricing, listing, or fulfillment issue specific to that product.`
      );
    }

    if (highestRevenueAnomaly) {
      businessReasons.push(
        `Order ${highestRevenueAnomaly.Order_ID} (${highestRevenueAnomaly.Product_Name}) has the largest revenue exposure at ${formatCurrency(
          highestRevenueAnomaly.Revenue
        )} — unusually large orders can indicate bulk-pricing errors or duplicate entries.`
      );
    }

    if (highestProfitAnomaly && highestProfitAnomaly.Profit < 0) {
      businessReasons.push(
        `Order ${highestProfitAnomaly.Order_ID} shows a loss of ${formatCurrency(
          Math.abs(highestProfitAnomaly.Profit)
        )}, which may reflect a discounting or cost-recording error.`
      );
    }

    businessReasons.push(
      repeatedProducts.length > 0
        ? "Recurring anomalies on the same product(s) suggest a systemic cause rather than isolated one-off errors — worth a root-cause review."
        : "Anomalies are spread across different products rather than concentrated on one — consistent with isolated transaction-level errors."
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
      <header
        style={{
          padding: "24px 28px",
          borderRadius: 16,
          background: `linear-gradient(135deg, ${COLORS.red} 0%, ${COLORS.orange} 100%)`,
          color: "white",
          boxShadow: "0 14px 30px rgba(220, 38, 38, 0.22)",
        }}
      >
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#fed7aa",
          }}
        >
          <Siren size={14} />
          Machine Learning Detection
        </span>
        <h1
          style={{
            fontSize: 28,
            fontWeight: 700,
            letterSpacing: "-0.02em",
            margin: "10px 0 6px",
          }}
        >
          Anomaly Detection Center
        </h1>
        <p style={{ color: "#fee2e2", fontSize: 14.5, maxWidth: 560 }}>
          Machine learning–flagged transactions that deviate from normal
          business patterns.
        </p>
      </header>

      {loading && (
        <div className="status-message">Loading anomaly data...</div>
      )}

      {error && <div className="error-message">{error}</div>}

      {!loading && !error && summary && (
        <>
          {/* ---------------- KPI STRIP ---------------- */}
          <section
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
              gap: 18,
            }}
          >
            <KpiCard
              icon={<Layers size={20} />}
              label="Total Transactions"
              value={formatNumber(summary.total_transactions)}
              accent={COLORS.ink}
            />

            <KpiCard
              icon={<AlertTriangle size={20} />}
              label="Total Anomalies"
              value={formatNumber(summary.anomaly_count)}
              accent={COLORS.red}
            />

            <KpiCard
              icon={<Percent size={20} />}
              label="Anomaly Percentage"
              value={`${summary.anomaly_percentage.toFixed(2)}%`}
              accent={COLORS.orange}
            />

            <KpiCard
              icon={<ListTree size={20} />}
              label="Features Used"
              value={featuresCount}
              subtitle={featuresList}
              accent={COLORS.yellow}
            />
          </section>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) 300px",
              gap: 22,
              alignItems: "start",
            }}
          >
            {/* ---------------- MAIN COLUMN ---------------- */}
            <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
              {/* Risk Level Badge */}
              <Panel>
                <SectionHeader
                  icon={<ShieldAlert size={14} />}
                  eyebrow="Business Risk"
                  title="Overall Risk Level"
                />

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 16,
                    padding: "16px 18px",
                    borderRadius: 12,
                    background: risk.bg,
                    borderLeft: `5px solid ${risk.color}`,
                  }}
                >
                  <span
                    style={{
                      padding: "6px 16px",
                      borderRadius: 999,
                      background: risk.color,
                      color: "white",
                      fontWeight: 700,
                      fontSize: 13,
                      letterSpacing: "0.02em",
                    }}
                  >
                    {overallRisk} Risk
                  </span>
                  <p style={{ fontSize: 13.5, color: COLORS.subtext, margin: 0 }}>
                    {risk.note}
                  </p>
                </div>
              </Panel>

              {/* Scatter Chart */}
              <Panel>
                <SectionHeader
                  icon={<AlertTriangle size={14} />}
                  eyebrow="Anomaly Landscape"
                  title="Revenue vs. Profit"
                />

                <p style={{ fontSize: 13, color: COLORS.subtext, marginBottom: 12 }}>
                  Each point is a flagged transaction. Color reflects relative
                  anomaly severity within this dataset.
                </p>

                {scatterData.length > 0 ? (
                  <div style={{ width: "100%", height: 320 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" />

                        <XAxis
                          type="number"
                          dataKey="revenue"
                          name="Revenue"
                          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
                          tick={{ fontSize: 11 }}
                        />

                        <YAxis
                          type="number"
                          dataKey="profit"
                          name="Profit"
                          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
                          tick={{ fontSize: 11 }}
                        />

                        <Tooltip
                          formatter={(value, name) => [
                            formatCurrency(value),
                            name === "revenue" ? "Revenue" : "Profit",
                          ]}
                          labelFormatter={() => ""}
                        />

                        <Scatter data={scatterData}>
                          {scatterData.map((point, index) => (
                            <Cell
                              key={index}
                              fill={RISK_META[getSeverity(point.score)].color}
                            />
                          ))}
                        </Scatter>
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="empty-state">
                    <AlertTriangle size={28} />
                    <h4>No anomalies to plot</h4>
                    <p>No flagged transactions were returned.</p>
                  </div>
                )}
              </Panel>

              {/* Top 10 Table */}
              <Panel>
                <SectionHeader
                  icon={<Layers size={14} />}
                  eyebrow="Suspicious Transactions"
                  title="Top 10 Anomalies"
                />

                {top10.length > 0 ? (
                  <div className="table-wrapper">
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                      <thead>
                        <tr>
                          {["Order ID", "Product", "Quantity", "Revenue", "Profit", "Anomaly Score"].map(
                            (heading, i) => (
                              <th
                                key={heading}
                                style={{
                                  textAlign: i === 0 ? "left" : "right",
                                  padding: "12px 14px",
                                  fontSize: 12,
                                  fontWeight: 700,
                                  letterSpacing: "0.04em",
                                  textTransform: "uppercase",
                                  color: COLORS.subtext,
                                  background: "#faf5f0",
                                  borderBottom: `1px solid ${COLORS.border}`,
                                }}
                              >
                                {heading}
                              </th>
                            )
                          )}
                        </tr>
                      </thead>

                      <tbody>
                        {top10.map((row, index) => {
                          const severity = getSeverity(row.Anomaly_Score);
                          return (
                            <tr key={row.Order_ID ?? index}>
                              <td style={cellStyle("left")}>{row.Order_ID}</td>
                              <td style={cellStyle("left")}>{row.Product_Name}</td>
                              <td style={cellStyle("right")}>
                                {formatNumber(row.Quantity)}
                              </td>
                              <td style={cellStyle("right")}>
                                {formatCurrency(row.Revenue)}
                              </td>
                              <td style={cellStyle("right")}>
                                {formatCurrency(row.Profit)}
                              </td>
                              <td
                                style={{
                                  ...cellStyle("right"),
                                  color: RISK_META[severity].color,
                                  fontWeight: 700,
                                }}
                              >
                                {row.Anomaly_Score.toFixed(3)}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty-state">
                    <Layers size={28} />
                    <h4>No suspicious transactions</h4>
                    <p>No flagged transactions were returned.</p>
                  </div>
                )}
              </Panel>

              {/* Business Risk Recommendations */}
              <Panel>
                <SectionHeader
                  icon={<Lightbulb size={14} />}
                  eyebrow="Business Risk Recommendations"
                  title="Possible Reasons Behind These Anomalies"
                />

                <ul style={{ display: "flex", flexDirection: "column", gap: 10, listStyle: "none" }}>
                  {businessReasons.map((text, index) => (
                    <li
                      key={index}
                      style={{
                        padding: "14px 16px",
                        borderRadius: 10,
                        background: "#fff7ed",
                        border: "1px solid #fed7aa",
                        fontSize: 14,
                        color: "#57534e",
                        lineHeight: 1.5,
                      }}
                    >
                      {text}
                    </li>
                  ))}
                </ul>
              </Panel>
            </div>

            {/* ---------------- DATASET HEALTH PANEL ---------------- */}
            <aside
              style={{
                background: COLORS.panelBg,
                border: `1px solid ${COLORS.border}`,
                borderRadius: 14,
                padding: 22,
                display: "flex",
                flexDirection: "column",
                gap: 14,
                boxShadow: "0 4px 16px rgba(28, 25, 23, 0.05)",
              }}
            >
              <h3
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontSize: 15,
                  fontWeight: 700,
                }}
              >
                <HeartPulse size={16} color={risk.color} />
                Dataset Health
              </h3>

              <HealthItem label="Overall Health" value={risk.health} valueColor={risk.color} />
              <HealthItem label="Total Anomalies" value={formatNumber(summary.anomaly_count)} />
              <HealthItem
                label="Features Used"
                value={featuresCount}
                sub={featuresList}
              />
              <HealthItem
                label="Highest Revenue Anomaly"
                value={
                  highestRevenueAnomaly
                    ? formatCurrency(highestRevenueAnomaly.Revenue)
                    : "—"
                }
                sub={highestRevenueAnomaly?.Order_ID}
              />
              <HealthItem
                label="Highest Profit Anomaly"
                value={
                  highestProfitAnomaly
                    ? formatCurrency(highestProfitAnomaly.Profit)
                    : "—"
                }
                sub={highestProfitAnomaly?.Order_ID}
              />
            </aside>
          </div>
        </>
      )}
    </div>
  );
}

function KpiCard({ icon, label, value, subtitle, accent }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        padding: 20,
        background: "white",
        border: "1px solid #e7e0d9",
        borderRadius: 14,
        borderTop: `3px solid ${accent}`,
        boxShadow: "0 4px 16px rgba(28, 25, 23, 0.05)",
      }}
    >
      <div
        style={{
          width: 34,
          height: 34,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 9,
          background: `${accent}1a`,
          color: accent,
        }}
      >
        {icon}
      </div>
      <span
        style={{
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: "0.03em",
          textTransform: "uppercase",
          color: "#78716c",
        }}
      >
        {label}
      </span>
      <strong style={{ fontSize: 24, fontWeight: 700, color: "#1c1917" }}>
        {value}
      </strong>
      {subtitle && (
        <span style={{ fontSize: 11.5, color: "#a8a29e" }}>{subtitle}</span>
      )}
    </div>
  );
}

function Panel({ children }) {
  return (
    <section
      style={{
        background: "white",
        border: "1px solid #e7e0d9",
        borderRadius: 16,
        padding: "24px 26px",
        boxShadow: "0 4px 18px rgba(28, 25, 23, 0.05)",
      }}
    >
      {children}
    </section>
  );
}

function SectionHeader({ icon, eyebrow, title }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        marginBottom: 18,
        paddingBottom: 14,
        borderBottom: "1px solid #f1ede7",
      }}
    >
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "#ea580c",
        }}
      >
        {icon}
        {eyebrow}
      </span>
      <h2 style={{ fontSize: 19, fontWeight: 700, letterSpacing: "-0.01em" }}>
        {title}
      </h2>
    </div>
  );
}

function HealthItem({ label, value, sub, valueColor }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        padding: "12px 14px",
        background: "#fff7ed",
        border: "1px solid #fed7aa",
        borderRadius: 10,
      }}
    >
      <span
        style={{
          fontSize: 11.5,
          fontWeight: 600,
          letterSpacing: "0.02em",
          textTransform: "uppercase",
          color: "#a8a29e",
        }}
      >
        {label}
      </span>
      <strong style={{ fontSize: 16, fontWeight: 700, color: valueColor ?? "#1c1917" }}>
        {value}
      </strong>
      {sub && <span style={{ fontSize: 11, color: "#a8a29e" }}>{sub}</span>}
    </div>
  );
}

function cellStyle(align) {
  return {
    textAlign: align,
    padding: "13px 14px",
    borderBottom: "1px solid #f1ede7",
    color: "#1c1917",
  };
}

export default Anomalies;