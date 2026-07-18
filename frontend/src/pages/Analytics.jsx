import { useEffect, useMemo, useState, useCallback } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import {
  Search,
  ArrowUpDown,
  ArrowUpRight,
  ArrowDownRight,
  Award,
  MapPin,
  Layers,
  TrendingUp,
  TrendingDown,
  Percent,
  Download,
  AlertCircle,
  RefreshCw,
  Inbox,
} from "lucide-react";

import { formatCurrency, formatNumber } from "../utils/format";
import { getDashboardOverview } from "../services/api";

const TEAL = "#0f766e";
const CYAN = "#0891b2";
const DONUT_COLORS = ["#0f766e", "#0891b2", "#14b8a6", "#06b6d4", "#2dd4bf", "#67e8f9"];

const PRODUCT_COLUMNS = [
  { key: "rank", label: "Rank" },
  { key: "product", label: "Product" },
  { key: "revenue", label: "Revenue" },
  { key: "profit", label: "Profit" },
  { key: "units", label: "Units" },
  { key: "growth", label: "Growth" },
];

// ---------------------------------------------------------------------
// Normalization — the ONE place backend PascalCase field names get
// converted to camelCase. Nothing else in this component should ever
// reference `p.Revenue` / `p.Product` etc. directly.
// ---------------------------------------------------------------------
function normalizeProduct(p) {
  return {
    rank: p.Rank,
    product: p.Product,
    revenue: p.Revenue,
    profit: p.Profit,
    units: p.Units,
    growth: p.Growth,
  };
}

// ---------------------------------------------------------------------
// Skeleton loading — scoped to this component only (no App.css changes).
// ---------------------------------------------------------------------
function SkeletonStyles() {
  return (
    <style>{`
      @keyframes ba-shimmer {
        0% { background-position: -400px 0; }
        100% { background-position: 400px 0; }
      }
      .ba-skel {
        background: linear-gradient(90deg, #f0fdfa 25%, #e6f7f5 37%, #f0fdfa 63%);
        background-size: 800px 100%;
        animation: ba-shimmer 1.4s ease-in-out infinite;
        border-radius: 10px;
      }
    `}</style>
  );
}

function Skeleton({ width = "100%", height = 16, style }) {
  return <div className="ba-skel" style={{ width, height, ...style }} />;
}

function SkeletonKpiCard() {
  return (
    <div className="ba-kpi-card">
      <Skeleton width="60%" height={11} />
      <Skeleton width="80%" height={22} style={{ marginTop: 8 }} />
    </div>
  );
}

function SkeletonPanel({ chartHeight = 260 }) {
  return (
    <section className="ba-panel">
      <Skeleton width="40%" height={12} />
      <Skeleton width="55%" height={20} style={{ marginTop: 10, marginBottom: 18 }} />
      <Skeleton height={chartHeight} />
    </section>
  );
}

function Panel({ children, className = "" }) {
  return <section className={`ba-panel ${className}`}>{children}</section>;
}

function SectionHeader({ eyebrow, title, caption }) {
  return (
    <div className="ba-section-header">
      <span className="ba-eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      {caption && <p className="ba-caption">{caption}</p>}
    </div>
  );
}

function KpiCard({ label, value }) {
  return (
    <div className="ba-kpi-card">
      <span className="ba-kpi-label">{label}</span>
      <strong className="ba-kpi-value">{value}</strong>
    </div>
  );
}

function InsightCard({ icon, title, value, sub }) {
  if (value === null || value === undefined) return null;

  return (
    <div className="ba-insight-card">
      <div className="ba-insight-icon">{icon}</div>
      <span className="ba-insight-label">{title}</span>
      <strong className="ba-insight-value">{value}</strong>
      {sub !== undefined && sub !== null && <span className="ba-insight-sub">{sub}</span>}
    </div>
  );
}

function Analytics() {
  const [year, setYear] = useState("All");
  const [month, setMonth] = useState("All");
  const [region, setRegion] = useState("All");
  const [category, setCategory] = useState("All");
  const [metric, setMetric] = useState("Revenue"); // "Revenue" | "Profit"

  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [productSearch, setProductSearch] = useState("");
  const [sortKey, setSortKey] = useState("rank");
  const [sortDir, setSortDir] = useState("asc");

  // Real backend filtering: every filter change triggers a fresh request.
  // No business-logic filtering happens on the client.
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);

      try {
        const res = await getDashboardOverview({ year, month, region, category });
        if (!cancelled) setResponse(res);
      } catch (err) {
        console.error(err);
        if (!cancelled) {
          setError(
            err?.response?.data?.message ||
              "Unable to load analytics data. Please try again."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [year, month, region, category]);

  const resetFilters = () => {
    setYear("All");
    setMonth("All");
    setRegion("All");
    setCategory("All");
  };

  const isEmpty = response?.empty === true;
  const data = response?.data ?? null;
  const filtersAvailable = response?.filters_available ?? {
    available_years: [],
    available_months: [],
    available_regions: [],
    available_categories: [],
  };

  const kpis = data?.kpis;
  const monthlyTrend = data?.monthly_trend ?? [];
  const categories = data?.categories ?? [];
  const regions = data?.regions ?? [];
  const insights = data?.insights;

  const hasProfitByMonth = monthlyTrend.length === 0 || monthlyTrend[0]?.Profit !== undefined;
  const hasProfitByRegion = regions.length === 0 || regions[0]?.Profit !== undefined;

  // Normalize once; every other computation reuses this.
  const normalizedProducts = useMemo(() => {
    return (data?.top_products ?? []).map(normalizeProduct);
  }, [data]);

  const filteredSortedProducts = useMemo(() => {
    const search = productSearch.trim().toLowerCase();
    let rows = search
      ? normalizedProducts.filter((p) => p.product?.toLowerCase().includes(search))
      : normalizedProducts;

    rows = [...rows].sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      const av = a[sortKey];
      const bv = b[sortKey];

      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;

      if (typeof av === "string") return av.localeCompare(bv) * dir;
      return (av - bv) * dir;
    });

    return rows;
  }, [normalizedProducts, productSearch, sortKey, sortDir]);

  const toggleSort = useCallback(
    (key) => {
      if (sortKey === key) {
        setSortDir((d) => (d === "asc" ? "desc" : "asc"));
      } else {
        setSortKey(key);
        setSortDir(key === "product" ? "asc" : "desc");
      }
    },
    [sortKey]
  );

  const donutData = useMemo(
    () => categories.map((c) => ({ name: c.Category, value: c.Revenue })),
    [categories]
  );

  const handleExportCsv = () => {
    if (!monthlyTrend.length) return;

    const header = hasProfitByMonth ? "Order_Date,Revenue,Profit\n" : "Order_Date,Revenue\n";
    const rows = monthlyTrend
      .map((r) =>
        hasProfitByMonth ? `${r.Order_Date},${r.Revenue},${r.Profit}` : `${r.Order_Date},${r.Revenue}`
      )
      .join("\n");

    const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "analytics-export.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  // Stubbed for now — same dispatch shape as CSV so enabling these later
  // is a one-line change, not a rewrite.
  const EXPORT_HANDLERS = {
    csv: handleExportCsv,
    pdf: () => console.info("PDF export not yet enabled."),
    excel: () => console.info("Excel export not yet enabled."),
  };

  const handleExport = (type) => EXPORT_HANDLERS[type]?.();

  const handleRetry = () => {
    // Re-triggers the effect by toggling a filter to itself via a fresh
    // fetch call directly (avoids depending on state identity changes).
    setError(null);
    setLoading(true);
    getDashboardOverview({ year, month, region, category })
      .then(setResponse)
      .catch((err) => {
        console.error(err);
        setError(err?.response?.data?.message || "Unable to load analytics data. Please try again.");
      })
      .finally(() => setLoading(false));
  };

  return (
    <div className="ba-page">
      <SkeletonStyles />

      <header className="ba-hero ba-fade-in">
        <span className="ba-hero-eyebrow">
          <Search size={14} />
          Deep Business Intelligence
        </span>
        <h1>Business Analytics</h1>
        <p>Explore, filter, and interrogate your business performance.</p>
      </header>

      {/* ---------------- FILTER BAR (options from filters_available) ---------------- */}
      <section className="filter-bar">
        <div className="filter-field">
          <label htmlFor="an-year">Year</label>
          <select id="an-year" value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="All">All Years</option>
            {filtersAvailable.available_years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="an-month">Month</label>
          <select id="an-month" value={month} onChange={(e) => setMonth(e.target.value)}>
            <option value="All">All Months</option>
            {filtersAvailable.available_months.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="an-region">Region</label>
          <select id="an-region" value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="All">All Regions</option>
            {filtersAvailable.available_regions.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="an-category">Category</label>
          <select id="an-category" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="All">All Categories</option>
            {filtersAvailable.available_categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <button className="filter-reset-button" onClick={resetFilters}>
          Reset Filters
        </button>
      </section>

      {/* ---------------- LOADING: SKELETON ---------------- */}
      {loading && (
        <>
          <section className="ba-kpi-grid ba-fade-in">
            <SkeletonKpiCard />
            <SkeletonKpiCard />
            <SkeletonKpiCard />
            <SkeletonKpiCard />
          </section>
          <SkeletonPanel chartHeight={300} />
          <div className="ba-two-col">
            <SkeletonPanel />
            <SkeletonPanel />
          </div>
          <SkeletonPanel chartHeight={220} />
        </>
      )}

      {/* ---------------- ERROR STATE ---------------- */}
      {!loading && error && (
        <div className="error-message" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
          <button
            onClick={handleRetry}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "8px 16px",
              borderRadius: 8,
              border: "none",
              background: "#dc2626",
              color: "white",
              fontWeight: 700,
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            <RefreshCw size={14} />
            Retry
          </button>
        </div>
      )}

      {/* ---------------- EMPTY STATE (backend-signaled only) ---------------- */}
      {!loading && !error && isEmpty && (
        <div
          className="ba-panel ba-fade-in"
          style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10, textAlign: "center", padding: "48px 24px" }}
        >
          <Inbox size={30} color={CYAN} />
          <strong style={{ fontSize: 16, color: "#134e4a" }}>No Data Available</strong>
          <p style={{ fontSize: 13.5, color: "#5f8a87", maxWidth: 360 }}>
            {response?.message || "No records match the selected filters."}
          </p>
        </div>
      )}

      {/* ---------------- MAIN CONTENT ---------------- */}
      {!loading && !error && !isEmpty && kpis && (
        <>
          <section className="ba-kpi-grid ba-fade-in">
            <KpiCard label="Total Revenue" value={formatCurrency(kpis.total_revenue)} />
            <KpiCard label="Total Profit" value={formatCurrency(kpis.total_profit)} />
            <KpiCard label="Profit Margin" value={`${kpis.profit_margin.toFixed(1)}%`} />
            <KpiCard label="Average Order Value" value={formatCurrency(kpis.average_order_value)} />
            {kpis.customer_count != null && (
              <KpiCard label="Customers" value={formatNumber(kpis.customer_count)} />
            )}
          </section>

          {/* ---------------- REVENUE EXPLORER ---------------- */}
          <Panel className="ba-fade-in">
            <SectionHeader
              eyebrow="Revenue Explorer"
              title="Revenue & Profit Over Time"
              caption="Toggle series, hover for exact values."
            />

            <div className="ba-toggle-group">
              <button
                className={`ba-toggle-btn ${metric === "Revenue" ? "ba-toggle-active" : ""}`}
                onClick={() => setMetric("Revenue")}
              >
                Revenue
              </button>
              <button
                className={`ba-toggle-btn ${metric === "Profit" ? "ba-toggle-active" : ""}`}
                onClick={() => setMetric("Profit")}
                disabled={!hasProfitByMonth}
              >
                Profit
              </button>
            </div>

            {monthlyTrend.length > 0 ? (
              <div className="ba-chart-lg">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={monthlyTrend}>
                    <defs>
                      <linearGradient id="baAreaGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={TEAL} stopOpacity={0.35} />
                        <stop offset="100%" stopColor={TEAL} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="Order_Date" tick={{ fontSize: 11 }} />
                    <YAxis tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v) => [formatCurrency(v), metric]} />
                    <Area
                      type="monotone"
                      dataKey={metric}
                      stroke={TEAL}
                      strokeWidth={2.5}
                      fill="url(#baAreaGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="ba-caption">No trend data for this selection.</p>
            )}
          </Panel>

          {/* ---------------- CATEGORY CONTRIBUTION + REGIONAL PERFORMANCE ---------------- */}
          <div className="ba-two-col">
            <Panel className="ba-fade-in">
              <SectionHeader
                eyebrow="Category Contribution"
                title="Top Categories"
                caption="Reacts to the Category filter."
              />

              {categories.length > 0 ? (
                <>
                  <div className="ba-chart-md">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={donutData} dataKey="value" nameKey="name" innerRadius="55%" outerRadius="85%" paddingAngle={2}>
                          {donutData.map((entry, i) => (
                            <Cell key={entry.name} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(v) => [formatCurrency(v), "Revenue"]} />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="ba-rank-list">
                    {categories.map((c, i) => (
                      <div className="ba-rank-row" key={c.Category}>
                        <span className="ba-rank-number">{i + 1}</span>
                        <div>
                          <div className="ba-rank-name">{c.Category}</div>
                          <div className="ba-rank-bar-track">
                            <div className="ba-rank-bar-fill" style={{ width: `${c.Contribution}%` }} />
                          </div>
                        </div>
                        <span className="ba-rank-value">{formatCurrency(c.Revenue)}</span>
                        <span className="ba-rank-pct">{c.Contribution.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="ba-caption">No category data for this selection.</p>
              )}
            </Panel>

            <Panel className="ba-fade-in">
              <SectionHeader eyebrow="Regional Performance" title="Revenue by Region" />

              {regions.length > 0 ? (
                <div className="ba-chart-md">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={regions} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} tick={{ fontSize: 11 }} />
                      <YAxis type="category" dataKey="Region" tick={{ fontSize: 12 }} width={70} />
                      <Tooltip formatter={(v) => formatCurrency(v)} />
                      {hasProfitByRegion && <Legend wrapperStyle={{ fontSize: 11 }} />}
                      <Bar dataKey="Revenue" fill={TEAL} radius={[0, 6, 6, 0]} />
                      {hasProfitByRegion && <Bar dataKey="Profit" fill={CYAN} radius={[0, 6, 6, 0]} />}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="ba-caption">No regional data for this selection.</p>
              )}
            </Panel>
          </div>

          {/* ---------------- PRODUCT INTELLIGENCE ---------------- */}
          <Panel className="ba-fade-in">
            <SectionHeader eyebrow="Product Intelligence" title="Top Products" />

            <div className="ba-search-wrap">
              <Search size={15} className="ba-search-icon" />
              <input
                type="text"
                placeholder="Search products..."
                value={productSearch}
                onChange={(e) => setProductSearch(e.target.value)}
                className="ba-search-input"
              />
            </div>

            {filteredSortedProducts.length > 0 ? (
              <div className="ba-table-scroll">
                <table className="ba-table">
                  <thead>
                    <tr>
                      {PRODUCT_COLUMNS.map((col) => (
                        <th key={col.key} onClick={() => toggleSort(col.key)}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                            {col.label}
                            <ArrowUpDown size={11} />
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSortedProducts.map((row) => (
                      <tr key={row.rank ?? row.product}>
                        <td>{row.rank}</td>
                        <td>{row.product}</td>
                        <td>{formatCurrency(row.revenue)}</td>
                        <td>{row.profit != null ? formatCurrency(row.profit) : "—"}</td>
                        <td>{row.units != null ? formatNumber(row.units) : "—"}</td>
                        <td>
                          {row.growth != null ? (
                            <span className={row.growth >= 0 ? "ba-growth-up" : "ba-growth-down"}>
                              {row.growth >= 0 ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
                              {Math.abs(row.growth).toFixed(1)}%
                            </span>
                          ) : (
                            "—"
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="ba-caption">
                {productSearch ? "No products match your search." : "No product data for this selection."}
              </p>
            )}
          </Panel>

          {/* ---------------- BUSINESS INSIGHTS ---------------- */}
          {insights && (
            <div className="ba-fade-in">
              <SectionHeader eyebrow="Business Insights" title="What The Data Shows" />

              <div className="ba-insight-grid">
                <InsightCard icon={<Award size={18} />} title="Highest Revenue Month" value={insights.highest_revenue_month} />
                <InsightCard icon={<TrendingDown size={18} />} title="Lowest Revenue Month" value={insights.lowest_revenue_month} />
                <InsightCard icon={<Award size={18} />} title="Highest Profit Month" value={insights.highest_profit_month} />
                <InsightCard icon={<TrendingDown size={18} />} title="Lowest Profit Month" value={insights.lowest_profit_month} />
                <InsightCard
                  icon={<TrendingUp size={18} />}
                  title="Fastest Growing Month"
                  value={insights.fastest_growing_month?.month}
                  sub={insights.fastest_growing_month ? `${insights.fastest_growing_month.change_pct}% growth` : undefined}
                />
                <InsightCard
                  icon={<TrendingUp size={18} />}
                  title="Largest Revenue Growth"
                  value={insights.largest_revenue_growth?.month}
                  sub={insights.largest_revenue_growth ? `${insights.largest_revenue_growth.change_pct}%` : undefined}
                />
                <InsightCard
                  icon={<TrendingDown size={18} />}
                  title="Largest Revenue Decline"
                  value={insights.largest_revenue_decline?.month}
                  sub={insights.largest_revenue_decline ? `${insights.largest_revenue_decline.change_pct}%` : undefined}
                />
                <InsightCard icon={<Layers size={18} />} title="Best Category" value={insights.best_category} />
                <InsightCard icon={<Layers size={18} />} title="Worst Category" value={insights.worst_category} />
                <InsightCard icon={<Percent size={18} />} title="Highest Profit Category" value={insights.highest_profit_category} />
                <InsightCard icon={<MapPin size={18} />} title="Best Region" value={insights.best_region} />
                <InsightCard icon={<MapPin size={18} />} title="Weakest Region" value={insights.weakest_region} />
                <InsightCard icon={<Percent size={18} />} title="Highest Profit Region" value={insights.highest_profit_region} />
                <InsightCard
                  icon={<Award size={18} />}
                  title="Average Order Value"
                  value={
                    insights.highest_average_order_value != null
                      ? formatCurrency(insights.highest_average_order_value)
                      : null
                  }
                />
              </div>
            </div>
          )}

          {/* ---------------- EXPORT CENTER ---------------- */}
          <section className="ba-export-section ba-fade-in">
            <button className="ba-export-button" onClick={() => handleExport("csv")}>
              <Download size={15} style={{ marginRight: 6 }} />
              Export CSV
            </button>
            <button
              className="ba-export-button ba-export-secondary"
              onClick={() => handleExport("pdf")}
              title="Coming soon"
            >
              Export PDF
            </button>
            <button
              className="ba-export-button ba-export-secondary"
              onClick={() => handleExport("excel")}
              title="Coming soon"
            >
              Export Excel
            </button>
          </section>
        </>
      )}
    </div>
  );
}

export default Analytics;