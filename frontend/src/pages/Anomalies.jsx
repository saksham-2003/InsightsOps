// src/pages/Anomalies.jsx
import React, { useEffect, useState, useMemo, useCallback } from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell as ScatterCell,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend
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
  Search,
  Download,
  FileText,
  Filter,
  ArrowUpDown,
  RefreshCw,
  Database,
  LineChart as LineChartIcon,
} from "lucide-react";

import { formatCurrency, formatNumber } from "../utils/format";
import { getAnomalies } from "../services/api";

const SEVERITY_META = {
  Critical: { color: "#dc2626", bg: "#fef2f2", order: 1 },
  High: { color: "#ea580c", bg: "#fff7ed", order: 2 },
  Medium: { color: "#ca8a04", bg: "#fefce8", order: 3 },
  Low: { color: "#16a34a", bg: "#f0fdf4", order: 4 },
};

function Anomalies() {
  const [anomalyData, setAnomalyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Filters State
  const [regionFilter, setRegionFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [severityFilter, setSeverityFilter] = useState("All");
  const [searchInput, setSearchInput] = useState("");

  // Debounced Search State
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchInput);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchInput]);

  // Table Sort/Pagination State
  const [sortKey, setSortKey] = useState("Severity_Score");
  const [sortDir, setSortDir] = useState("desc");
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const loadAnomalies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getAnomalies({
        region: regionFilter,
        category: categoryFilter,
        startDate,
        endDate,
        severity: severityFilter,
        search: debouncedSearch
      });

      if (response.success === false) {
        setError(response.message || "Failed to load anomaly data.");
        if (isInitialLoad) setAnomalyData(null);
      } else {
        setAnomalyData(response.data);
      }
    } catch (err) {
      console.error(err);
      setError("Unable to load anomaly data. Check backend connection.");
      if (isInitialLoad) setAnomalyData(null);
    } finally {
      setLoading(false);
      setIsInitialLoad(false);
    }
  }, [regionFilter, categoryFilter, startDate, endDate, severityFilter, debouncedSearch, isInitialLoad]);

  useEffect(() => {
    loadAnomalies();
  }, [loadAnomalies]);

  const resetFilters = () => {
    setRegionFilter("All");
    setCategoryFilter("All");
    setStartDate("");
    setEndDate("");
    setSeverityFilter("All");
    setSearchInput("");
  };

  const {
    executive_summary,
    kpis,
    charts,
    table_data = [],
    recommendations,
    filter_options
  } = anomalyData || {};

  const sortedTableData = useMemo(() => {
    if (!table_data.length) return [];
    return [...table_data].sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      let valA = a[sortKey];
      let valB = b[sortKey];
      if (typeof valA === "string") return valA.localeCompare(valB) * dir;
      return ((valA || 0) - (valB || 0)) * dir;
    });
  }, [table_data, sortKey, sortDir]);

  const paginatedTableData = useMemo(() => {
    const startIndex = (currentPage - 1) * rowsPerPage;
    return sortedTableData.slice(startIndex, startIndex + rowsPerPage);
  }, [sortedTableData, currentPage]);

  const totalPages = Math.ceil(sortedTableData.length / rowsPerPage);

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
    setCurrentPage(1);
  };

  const scatterData = useMemo(() => {
    return table_data.map((row) => ({
      revenue: row.Revenue,
      profit: row.Profit,
      score: row.Severity_Score,
      severity: row.Severity,
      product: row.Product_Name,
    }));
  }, [table_data]);

  const riskColor = SEVERITY_META[executive_summary?.business_risk]?.color || "#ea580c";
  const riskBg = SEVERITY_META[executive_summary?.business_risk]?.bg || "#fff7ed";

  const handleExportCsv = useCallback(() => {
    if (!table_data.length) return;
    const header = "Order_Date,Region,Category,Product_Name,Revenue,Profit,Severity_Score,Severity,Reason\n";
    const rows = table_data.map((r) => [
      r.Order_Date,
      `"${r.Region}"`,
      `"${r.Category}"`,
      `"${r.Product_Name}"`,
      r.Revenue,
      r.Profit,
      r.Severity_Score.toFixed(2),
      r.Severity,
      `"${r.Reason}"`
    ].join(",")).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "anomaly-report.csv";
    link.click();
    URL.revokeObjectURL(url);
  }, [table_data]);

  const handleExportPdf = useCallback(async () => {
    if (!table_data.length) return;
    try {
      const { jsPDF } = await import("jspdf");
      const autoTable = (await import("jspdf-autotable")).default;
      const doc = new jsPDF("landscape");
      
      let y = 16;
      doc.setFontSize(16);
      doc.text("Anomaly Detection Report", 14, y);
      y += 10;

      doc.setFontSize(10);
      doc.text(`Total Anomalies: ${executive_summary.total_anomalies}`, 14, y);
      doc.text(`Business Risk: ${executive_summary.business_risk}`, 80, y);
      y += 8;

      autoTable(doc, {
        startY: y,
        head: [["Date", "Region", "Category", "Product", "Revenue", "Severity", "Reason"]],
        body: table_data.slice(0, 100).map((r) => [
          r.Order_Date, r.Region, r.Category, r.Product_Name,
          formatCurrency(r.Revenue), r.Severity, r.Reason
        ]),
        styles: { fontSize: 8 },
        columnStyles: { 6: { cellWidth: 80 } }
      });
      doc.save("anomaly-report.pdf");
    } catch (err) {
      console.error(err);
      alert("PDF export requires 'jspdf' and 'jspdf-autotable'. npm install jspdf jspdf-autotable");
    }
  }, [table_data, executive_summary]);

  if (isInitialLoad && loading) {
    return (
      <div className="anm-page anm-fade-in">
        <header className="anm-hero">
          <span className="anm-eyebrow"><Siren size={14} /> Machine Learning Detection</span>
          <h1>Anomaly Detection Center</h1>
          <p>Scanning transactions for pattern deviations and risk exposure.</p>
        </header>
        <div className="anm-skeleton-strip">
          <div className="anm-skeleton-card"></div><div className="anm-skeleton-card"></div><div className="anm-skeleton-card"></div><div className="anm-skeleton-card"></div>
        </div>
        <div className="anm-panel anm-skeleton-chart"></div>
      </div>
    );
  }

  return (
    <div className="anm-page anm-fade-in">
      <style>{`
        .anm-page { display: flex; flex-direction: column; gap: 24px; }
        .anm-fade-in { animation: anmFadeIn 0.4s ease-out; }
        @keyframes anmFadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        /* Hero matching InsightsOps dark blue theme requested */
        .anm-hero {
          background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 55%, #312e81 100%);
          border-radius: 16px;
          padding: 28px 32px;
          color: white;
          box-shadow: 0 14px 34px rgba(15, 23, 42, 0.22);
          position: relative;
          overflow: hidden;
        }
        .anm-hero::after {
          content: ""; position: absolute; top: -50%; right: -10%; width: 300px; height: 300px;
          background: radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%); border-radius: 50%;
        }
        .anm-eyebrow { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #a5b4fc; }
        .anm-hero h1 { font-size: 28px; font-weight: 700; letter-spacing: -0.02em; margin: 10px 0 6px; color: white; }
        .anm-hero p { color: #cbd5e1; font-size: 14.5px; max-width: 580px; }

        /* Controls */
        .anm-controls { background: white; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04); display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end; }
        .anm-control-group { display: flex; flex-direction: column; gap: 6px; min-width: 150px; flex: 1; }
        .anm-control-group label { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.04em; }
        .anm-input, .anm-select { padding: 10px 14px; border-radius: 8px; border: 1px solid #cbd5e1; background-color: #f8fafc; font-size: 14px; color: #0f172a; transition: all 0.2s; outline: none; }
        .anm-input:focus, .anm-select:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }
        .anm-btn-reset { padding: 10px 18px; border-radius: 8px; background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155; font-weight: 600; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }
        .anm-btn-reset:hover { background: #e2e8f0; }

        /* KPI Strip */
        .anm-kpi-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }
        .anm-kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px; display: flex; flex-direction: column; gap: 6px; box-shadow: 0 4px 16px rgba(15,23,42,0.04); transition: transform 0.2s, box-shadow 0.2s; }
        .anm-kpi-card:hover { transform: translateY(-3px); box-shadow: 0 12px 24px rgba(15,23,42,0.08); border-color: #c7d2fe; }
        .anm-kpi-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-bottom: 4px; }
        .anm-kpi-label { font-size: 12px; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; color: #64748b; }
        .anm-kpi-value { font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.01em; }

        /* Panels */
        .anm-panel { background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; box-shadow: 0 4px 18px rgba(15,23,42,0.05); }
        .anm-panel-header { margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 6px; }
        .anm-panel-eyebrow { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #6366f1; }
        .anm-panel-title { font-size: 19px; font-weight: 700; color: #1e293b; letter-spacing: -0.01em; }
        
        /* Grid Layouts */
        .anm-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
        @media(max-width: 900px) { .anm-grid-2 { grid-template-columns: 1fr; } }
        
        .anm-chart-wrap { height: 300px; width: 100%; margin-top: 10px; }

        /* Table */
        .anm-table-wrap { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 12px; }
        .anm-table { width: 100%; border-collapse: collapse; font-size: 14px; }
        .anm-table th { padding: 12px 14px; background: #f8fafc; font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748b; border-bottom: 1px solid #e2e8f0; cursor: pointer; user-select: none; text-align: left; position: sticky; top: 0; }
        .anm-table td { padding: 14px; border-bottom: 1px solid #f1f5f9; color: #1e293b; }
        .anm-table tr:hover td { background: #f8fafc; }
        .anm-severity-badge { display: inline-flex; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
        
        .anm-pagination { display: flex; justify-content: space-between; align-items: center; padding: 12px 0 0; font-size: 14px; color: #64748b; }
        .anm-page-btns { display: flex; gap: 8px; }
        .anm-page-btn { padding: 6px 12px; border: 1px solid #e2e8f0; background: white; border-radius: 6px; cursor: pointer; font-weight: 600; color: #334155; }
        .anm-page-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .anm-page-btn:not(:disabled):hover { background: #f1f5f9; }

        /* Reason list */
        .anm-reason-list { display: flex; flex-direction: column; gap: 10px; list-style: none; }
        .anm-reason-item { padding: 14px 16px; border-radius: 10px; font-size: 14.5px; color: #334155; line-height: 1.5; display: flex; gap: 10px; align-items: flex-start; }

        /* Loader Overlay */
        .anm-data-wrapper { position: relative; transition: opacity 0.3s ease; display: flex; flex-direction: column; gap: 24px; }
        .anm-data-wrapper.is-loading { opacity: 0.5; pointer-events: none; }
        .anm-loading-overlay { position: absolute; top: 20%; left: 50%; transform: translate(-50%, -50%); z-index: 10; display: flex; flex-direction: column; align-items: center; gap: 12px; background: white; padding: 24px 36px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); color: #6366f1; font-weight: 600; }

        /* Skeleton */
        @keyframes pulse { 50% { opacity: 0.5; } }
        .anm-skeleton-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-bottom: 22px; }
        .anm-skeleton-card { height: 110px; background: #e2e8f0; border-radius: 14px; animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        .anm-skeleton-chart { height: 400px; background: #e2e8f0; animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
      `}</style>

      {error && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, background: "#fef2f2", border: "1px solid #fecaca", color: "#b91c1c", padding: "12px 16px", borderRadius: 10, fontWeight: 600 }}>
          <AlertTriangle size={18} />
          <span>{error}</span>
          <button onClick={loadAnomalies} className="anm-btn-reset" style={{ marginLeft: "auto", background: "white", color: "#b91c1c", borderColor: "#fca5a5" }}>
            <RefreshCw size={14} /> Retry
          </button>
        </div>
      )}

      {executive_summary && (
        <div className={`anm-data-wrapper ${!isInitialLoad && loading ? 'is-loading' : ''}`}>
          {!isInitialLoad && loading && (
            <div className="anm-loading-overlay">
              <RefreshCw size={32} className="fx-spin-icon" style={{ animation: "pulse 1s linear infinite" }} />
              <span>Analyzing Transactions...</span>
            </div>
          )}

          {/* CONTROLS */}
          <section className="anm-controls">
            <div className="anm-control-group">
              <label>Region</label>
              <select className="anm-select" value={regionFilter} onChange={e => setRegionFilter(e.target.value)}>
                <option value="All">All Regions</option>
                {filter_options?.regions?.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div className="anm-control-group">
              <label>Category</label>
              <select className="anm-select" value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
                <option value="All">All Categories</option>
                {filter_options?.categories?.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="anm-control-group">
              <label>Start Date</label>
              <input type="date" className="anm-input" value={startDate} onChange={e => setStartDate(e.target.value)} />
            </div>
            <div className="anm-control-group">
              <label>End Date</label>
              <input type="date" className="anm-input" value={endDate} onChange={e => setEndDate(e.target.value)} />
            </div>
            <div className="anm-control-group">
              <label>Severity</label>
              <select className="anm-select" value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}>
                <option value="All">All Severities</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
            <div className="anm-control-group" style={{ position: "relative", minWidth: 200 }}>
              <Search size={15} style={{ position: "absolute", left: 12, top: 32, color: "#94a3b8" }} />
              <label>Search Product</label>
              <input type="text" className="anm-input" style={{ paddingLeft: 34 }} placeholder="Search product..." value={searchInput} onChange={e => setSearchInput(e.target.value)} />
            </div>
            <button className="anm-btn-reset" onClick={resetFilters}><Filter size={15} /> Reset</button>
          </section>

          {/* EXECUTIVE SUMMARY */}
          {executive_summary.total_anomalies === 0 ? (
            <div className="anm-panel" style={{ textAlign: "center", padding: "60px 20px" }}>
              <ShieldAlert size={48} color="#10b981" style={{ margin: "0 auto 16px" }} />
              <h2 style={{ fontSize: 24, color: "#064e3b" }}>No Anomalies Detected</h2>
              <p style={{ color: "#047857" }}>The current filter criteria returned no suspicious transactions.</p>
            </div>
          ) : (
            <>
              {/* EXEC SUMMARY BANNER */}
              <div className="anm-panel" style={{ background: riskBg, borderLeft: `6px solid ${riskColor}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
                  <div>
                    <h3 style={{ fontSize: 20, color: riskColor, fontWeight: 800, marginBottom: 8 }}>{executive_summary.business_risk} Risk Profile</h3>
                    <p style={{ color: "#475569", fontSize: 14 }}>Detected <strong>{formatNumber(executive_summary.total_anomalies)} anomalies</strong> affecting <strong>{executive_summary.anomaly_percentage.toFixed(2)}%</strong> of selected transactions.</p>
                  </div>
                  <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>Max Severity Score</span>
                      <strong style={{ fontSize: 22, color: "#0f172a" }}>{executive_summary.highest_score.toFixed(1)}</strong>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>Avg Anomaly Value</span>
                      <strong style={{ fontSize: 22, color: "#0f172a" }}>{formatCurrency(executive_summary.avg_anomaly_value)}</strong>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>Top Affected Area</span>
                      <strong style={{ fontSize: 16, color: "#0f172a", marginTop: 4 }}>{executive_summary.most_affected_region} / {executive_summary.most_affected_category}</strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* KPIs */}
              <section className="anm-kpi-strip">
                <KpiCard icon={<Layers />} label="Total Transactions" value={formatNumber(kpis.total_transactions)} accent="#6366f1" />
                <KpiCard icon={<Percent />} label="Normal Records" value={formatNumber(kpis.normal_records)} accent="#10b981" />
                <KpiCard icon={<AlertTriangle />} label="Total Anomalies" value={formatNumber(kpis.anomalies)} accent="#ef4444" />
                <KpiCard icon={<HeartPulse />} label="Anomaly %" value={`${kpis.anomaly_percentage.toFixed(2)}%`} accent="#f59e0b" />
              </section>

              {/* CHARTS GRID */}
              <div className="anm-grid-2">
                {/* Monthly Trend */}
                <div className="anm-panel">
                  <div className="anm-panel-header">
                    <span className="anm-panel-eyebrow"><LineChart size={14}/> Timeline</span>
                    <h2 className="anm-panel-title">Monthly Anomaly Trend</h2>
                  </div>
                  <div className="anm-chart-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={charts.monthly_trend}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="Month" tick={{ fontSize: 12 }} />
                        <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                        <Tooltip />
                        <Line type="monotone" dataKey="Count" stroke="#ef4444" strokeWidth={3} dot={{ r: 4, fill: "#ef4444" }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Scatter Plot */}
                <div className="anm-panel">
                  <div className="anm-panel-header">
                    <span className="anm-panel-eyebrow"><Database size={14}/> Scatter</span>
                    <h2 className="anm-panel-title">Revenue vs Profit (Anomalies)</h2>
                  </div>
                  <div className="anm-chart-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" dataKey="revenue" name="Revenue" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                        <YAxis type="number" dataKey="profit" name="Profit" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(val, name) => [formatCurrency(val), name === "revenue" ? "Revenue" : "Profit"]} labelFormatter={() => ""} />
                        <Scatter data={scatterData}>
                          {scatterData.map((entry, index) => (
                            <ScatterCell key={`cell-${index}`} fill={SEVERITY_META[entry.severity]?.color || "#6366f1"} />
                          ))}
                        </Scatter>
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Region & Category Distribution */}
                <div className="anm-panel">
                  <div className="anm-panel-header">
                    <span className="anm-panel-eyebrow"><ListTree size={14}/> Distribution</span>
                    <h2 className="anm-panel-title">Anomalies by Region & Category</h2>
                  </div>
                  <div className="anm-chart-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={charts.region_distribution}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="Region" tick={{ fontSize: 12 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                        <Tooltip />
                        <Bar dataKey="Count" fill="#6366f1" radius={[4,4,0,0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Severity Distribution */}
                <div className="anm-panel">
                  <div className="anm-panel-header">
                    <span className="anm-panel-eyebrow"><ShieldAlert size={14}/> Severity</span>
                    <h2 className="anm-panel-title">Severity Breakdown</h2>
                  </div>
                  <div className="anm-chart-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={charts.severity_distribution} dataKey="Count" nameKey="Severity" innerRadius="55%" outerRadius="85%">
                          {charts.severity_distribution.map((entry, i) => (
                            <Cell key={`pie-${i}`} fill={SEVERITY_META[entry.Severity]?.color || "#94a3b8"} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* TABLE */}
              <div className="anm-panel">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <div className="anm-panel-header" style={{ marginBottom: 0, paddingBottom: 0, borderBottom: "none" }}>
                    <span className="anm-panel-eyebrow"><ListTree size={16} /> Data</span>
                    <h2 className="anm-panel-title">Suspicious Transactions Log</h2>
                  </div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <button className="anm-btn-reset" onClick={handleExportCsv}><Download size={14} /> CSV</button>
                    <button className="anm-btn-reset" onClick={handleExportPdf} style={{ background: "#6366f1", color: "white", borderColor: "#6366f1" }}><FileText size={14} /> PDF</button>
                  </div>
                </div>

                <div className="anm-table-wrap">
                  <table className="anm-table">
                    <thead>
                      <tr>
                        {[{key: "Order_Date", label: "Date"}, {key: "Region", label: "Region"}, {key: "Category", label: "Category"}, {key: "Product_Name", label: "Product"}, {key: "Revenue", label: "Revenue"}, {key: "Profit", label: "Profit"}, {key: "Severity_Score", label: "Severity"}, {key: "Reason", label: "AI Reason"}].map(col => (
                          <th key={col.key} onClick={() => toggleSort(col.key)}>
                            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                              {col.label} <ArrowUpDown size={12} />
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedTableData.map((row, i) => (
                        <tr key={row.Order_ID || i}>
                          <td style={{ whiteSpace: "nowrap" }}>{row.Order_Date}</td>
                          <td>{row.Region}</td>
                          <td>{row.Category}</td>
                          <td>{row.Product_Name}</td>
                          <td style={{ fontWeight: 600 }}>{formatCurrency(row.Revenue)}</td>
                          <td style={{ color: row.Profit < 0 ? "#ef4444" : "inherit" }}>{formatCurrency(row.Profit)}</td>
                          <td>
                            <span className="anm-severity-badge" style={{ background: SEVERITY_META[row.Severity]?.bg, color: SEVERITY_META[row.Severity]?.color, border: `1px solid ${SEVERITY_META[row.Severity]?.color}40` }}>
                              {row.Severity} ({row.Severity_Score.toFixed(1)})
                            </span>
                          </td>
                          <td style={{ fontSize: 13, color: "#64748b", maxWidth: 300 }}>{row.Reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {totalPages > 1 && (
                  <div className="anm-pagination">
                    <span>Showing {(currentPage - 1) * rowsPerPage + 1} to {Math.min(currentPage * rowsPerPage, sortedTableData.length)} of {sortedTableData.length} records</span>
                    <div className="anm-page-btns">
                      <button className="anm-page-btn" disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)}>Prev</button>
                      <span style={{ padding: "6px 12px", fontWeight: 600 }}>{currentPage} / {totalPages}</span>
                      <button className="anm-page-btn" disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)}>Next</button>
                    </div>
                  </div>
                )}
              </div>

              {/* RECOMMENDATIONS */}
              <div className="anm-panel">
                <div className="anm-panel-header">
                  <span className="anm-panel-eyebrow"><Lightbulb size={14}/> Actionable Insights</span>
                  <h2 className="anm-panel-title">Business Recommendations</h2>
                </div>
                <ul className="anm-reason-list">
                  {recommendations.map((rec, i) => (
                    <li key={i} className="anm-reason-item" style={{ background: "#f8fafc", border: "1px solid #e2e8f0" }}>
                      <Lightbulb size={18} color="#6366f1" style={{ flexShrink: 0 }} />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function KpiCard({ icon, label, value, accent }) {
  return (
    <div className="anm-kpi-card" style={{ borderTop: `4px solid ${accent}` }}>
      <div className="anm-kpi-icon" style={{ background: `${accent}15`, color: accent }}>{icon}</div>
      <span className="anm-kpi-label">{label}</span>
      <strong className="anm-kpi-value">{value}</strong>
    </div>
  );
}

export default Anomalies;