// src/pages/Forecasting.jsx
import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  BarChart,
  Bar,
  Cell,
  ScatterChart,
  Scatter,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  ReferenceLine,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Activity,
  Gauge,
  Sparkles,
  Radar,
  AlertTriangle,
  ClipboardList,
  HeartPulse,
  ListChecks,
  Lightbulb,
  LineChart as LineChartIcon,
  SlidersHorizontal,
  Search,
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  Download,
  FileText,
  RefreshCw,
  Info,
} from "lucide-react";

import { formatCurrency, formatNumber } from "../utils/format";
import { getForecastEvaluation, getDashboardOverview } from "../services/api";

const MODEL_HEALTH_TIERS = {
  "Very High": {
    label: "Excellent Model",
    reliability: "Very High",
    note: "Suitable for both short-term and medium-term business planning.",
    recommendation: "Very high confidence forecasting model. Forecast is suitable for both short-term and medium-term business planning.",
    className: "fx-health-excellent",
    color: "#12b76a",
  },
  High: {
    label: "Strong Model",
    reliability: "High",
    note: "Suitable for short-term business planning.",
    recommendation: "High confidence forecasting model. Forecast is suitable for short-term business planning.",
    className: "fx-health-strong",
    color: "#12b76a",
  },
  Medium: {
    label: "Moderate Model",
    reliability: "Medium",
    note: "Use as a directional guide and validate against other signals.",
    recommendation: "Medium confidence forecasting model. Use the forecast as a directional guide and validate against other signals before committing to plans.",
    className: "fx-health-moderate",
    color: "#f79009",
  },
  Low: {
    label: "Needs Improvement",
    reliability: "Low",
    note: "Treat forecasts as indicative only.",
    recommendation: "Low confidence forecasting model. Treat the forecast as indicative only and avoid relying on it for planning decisions.",
    className: "fx-health-weak",
    color: "#f04438",
  },
};

const getModelHealthTier = (r2) => {
  if (r2 >= 0.9) return "Very High";
  if (r2 >= 0.8) return "High";
  if (r2 >= 0.7) return "Medium";
  return "Low";
};

const HORIZON_OPTIONS = [
  { value: "7", label: "7 Days" },
  { value: "30", label: "30 Days" },
  { value: "90", label: "90 Days" },
  { value: "custom", label: "Custom" },
];

const formatDate = (dateStr) => {
  if (!dateStr) return "—";
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return dateStr;
  return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
};

const formatSignedCurrency = (value) => {
  if (value == null) return "—";
  const sign = value < 0 ? "-" : "";
  return `${sign}${formatCurrency(Math.abs(value))}`;
};

const average = (arr) => (arr.length ? arr.reduce((s, v) => s + v, 0) / arr.length : 0);

const getErrorSeverityClass = (absError, avgAbsError) => {
  if (absError == null) return "";
  if (avgAbsError === 0) return "fx-error-good";
  if (absError <= avgAbsError) return "fx-error-good";
  if (absError <= avgAbsError * 1.5) return "fx-error-warning";
  return "fx-error-bad";
};

const getErrorSeverityColor = (absError, avgAbsError) => {
  if (absError == null) return "#98a2b3";
  if (avgAbsError === 0) return "#12b76a";
  if (absError <= avgAbsError) return "#12b76a";
  if (absError <= avgAbsError * 1.5) return "#f79009";
  return "#f04438";
};

const buildDistribution = (values, bucketCount = 6) => {
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) return [{ range: formatCurrency(min), count: values.length }];

  const bucketSize = (max - min) / bucketCount;
  const buckets = Array.from({ length: bucketCount }, (_, i) => ({
    rangeStart: min + i * bucketSize,
    rangeEnd: min + (i + 1) * bucketSize,
    count: 0,
  }));

  values.forEach((value) => {
    let idx = Math.floor((value - min) / bucketSize);
    if (idx >= bucketCount) idx = bucketCount - 1;
    if (idx < 0) idx = 0;
    buckets[idx].count += 1;
  });

  return buckets.map((b) => ({
    range: `${formatCurrency(b.rangeStart)}–${formatCurrency(b.rangeEnd)}`,
    count: b.count,
  }));
};

function calculateTrend(predictions) {
  if (!predictions || !predictions.length) return null;

  const n = predictions.length;
  const half = Math.max(1, Math.floor(n / 2));
  const firstHalfAvg = average(predictions.slice(0, half).map((p) => p.Predicted_Revenue));
  const secondHalfAvg = average(predictions.slice(n - half).map((p) => p.Predicted_Revenue));
  const growthPct = firstHalfAvg ? ((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100 : 0;

  const direction = growthPct > 3 ? "Increasing" : growthPct < -3 ? "Declining" : "Stable";

  const peak = predictions.reduce(
    (best, curr) => (!best || curr.Predicted_Revenue > best.Predicted_Revenue ? curr : best),
    null
  );
  const low = predictions.reduce(
    (worst, curr) => (!worst || curr.Predicted_Revenue < worst.Predicted_Revenue ? curr : worst),
    null
  );

  return {
    direction,
    growthPct: Number(growthPct.toFixed(1)),
    peakDate: peak?.Order_Date,
    peakValue: peak?.Predicted_Revenue,
    lowDate: low?.Order_Date,
    lowValue: low?.Predicted_Revenue,
    avgDaily: average(predictions.map((p) => p.Predicted_Revenue)),
  };
}

const TREND_ICON = { Increasing: TrendingUp, Declining: TrendingDown, Stable: Minus };
const TREND_COLOR = { Increasing: "#12b76a", Declining: "#f04438", Stable: "#98a2b3" };

function ScatterTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="fx-tooltip">
      <p className="fx-tooltip-date">{formatDate(point.date)}</p>
      <p>Actual: {formatCurrency(point.actual)}</p>
      <p>Predicted: {formatCurrency(point.predicted)}</p>
    </div>
  );
}

function Forecasting() {
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [availableRegions, setAvailableRegions] = useState([]);
  const [availableCategories, setAvailableCategories] = useState([]);

  const [horizon, setHorizon] = useState("30");
  const [customDate, setCustomDate] = useState("");
  const [regionFilter, setRegionFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");

  const [showHistorical, setShowHistorical] = useState(true);
  const [showForecastLine, setShowForecastLine] = useState(true);
  const [showConfidenceBand, setShowConfidenceBand] = useState(true);
  const [scenario, setScenario] = useState("expected");

  const [modelInfoOpen, setModelInfoOpen] = useState(false);
  const [tableSearch, setTableSearch] = useState("");
  const [sortKey, setSortKey] = useState("Order_Date");
  const [sortDir, setSortDir] = useState("desc"); // Defaults to showing latest future first

  // Initialize filter dropdowns
  useEffect(() => {
    getDashboardOverview().then(res => {
      const data = res.data || res;
      if (data.regions) setAvailableRegions(data.regions.map(r => r.Region));
      if (data.categories) setAvailableCategories(data.categories.map(c => c.Category));
    }).catch(console.error);
  }, []);

  const loadForecast = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getForecastEvaluation({
        horizon,
        region: regionFilter,
        category: categoryFilter,
        customDate,
      });

      if (response.success === false) {
        setError(response.message || "No data available for the selected filters.");
        setForecastData(null);
      } else {
        setForecastData(response.data || response);
      }
    } catch (err) {
      console.error(err);
      setError("Unable to load forecast data. Please verify backend connection.");
    } finally {
      setLoading(false);
    }
  }, [horizon, regionFilter, categoryFilter, customDate]);

  useEffect(() => {
    loadForecast();
  }, [loadForecast]);

  const metrics = forecastData?.metrics;
  const predictions = useMemo(() => forecastData?.predictions ?? [], [forecastData]);

  const predictedRevenueTotal = useMemo(
    () => predictions.reduce((sum, row) => sum + (row.Predicted_Revenue ?? 0), 0),
    [predictions]
  );

  const averagePredictedRevenue = predictions.length ? predictedRevenueTotal / predictions.length : 0;

  const forecastPeriod = predictions.length > 0
    ? `${formatDate(predictions[0].Order_Date)} → ${formatDate(predictions[predictions.length - 1].Order_Date)}`
    : "—";

  const bestForecastDay = useMemo(
    () => predictions.reduce((best, curr) => (!best || curr.Predicted_Revenue > best.Predicted_Revenue ? curr : best), null),
    [predictions]
  );

  const lowestForecastDay = useMemo(
    () => predictions.reduce((lowest, curr) => (!lowest || curr.Predicted_Revenue < lowest.Predicted_Revenue ? curr : lowest), null),
    [predictions]
  );

  const predictionsWithError = useMemo(
    () => predictions.map((row) => ({
      ...row,
      error: row.Revenue != null ? row.Revenue - row.Predicted_Revenue : null 
    })),
    [predictions]
  );

  const validErrors = useMemo(
    () => predictionsWithError.filter((r) => r.error != null),
    [predictionsWithError]
  );

  const avgAbsError = useMemo(
    () => validErrors.length ? validErrors.reduce((sum, row) => sum + Math.abs(row.error), 0) / validErrors.length : 0,
    [validErrors]
  );

  const overallBias = useMemo(
    () => validErrors.length ? validErrors.reduce((sum, row) => sum + row.error, 0) / validErrors.length : 0,
    [validErrors]
  );

  const worstForecastDay = useMemo(
    () => validErrors.reduce((worst, curr) => (!worst || Math.abs(curr.error) > Math.abs(worst.error) ? curr : worst), null),
    [validErrors]
  );

  const highVarianceDays = useMemo(
    () => validErrors.filter((row) => Math.abs(row.error) > avgAbsError * 1.5),
    [validErrors, avgAbsError]
  );

  const healthTier = metrics ? getModelHealthTier(metrics.R2) : null;
  const health = healthTier ? MODEL_HEALTH_TIERS[healthTier] : null;
  const trend = useMemo(() => calculateTrend(predictions), [predictions]);
  const TrendIcon = trend ? TREND_ICON[trend.direction] : Minus;

  const chartData = useMemo(() => {
    const mae = metrics?.MAE ?? 0;
    return predictions.map((p) => {
      const best = p.Predicted_Revenue + mae;
      const expected = p.Predicted_Revenue;
      const worst = Math.max(0, p.Predicted_Revenue - mae);
      const scenarioValue = scenario === "best" ? best : scenario === "worst" ? worst : expected;
      return {
        ...p,
        best,
        expected,
        worst,
        scenarioValue,
        confidenceBand: [worst, best],
      };
    });
  }, [predictions, metrics, scenario]);

  const scatterData = useMemo(
    () => validErrors.map((row) => ({ actual: row.Revenue, predicted: row.Predicted_Revenue, date: row.Order_Date })),
    [validErrors]
  );

  const scatterValues = scatterData.flatMap((p) => [p.actual, p.predicted]);
  const scatterMin = scatterValues.length ? Math.min(...scatterValues) : 0;
  const scatterMax = scatterValues.length ? Math.max(...scatterValues) : 0;

  const errorChartData = useMemo(
    () => validErrors.map((row) => ({ date: formatDate(row.Order_Date), error: row.error })),
    [validErrors]
  );

  const distributionData = useMemo(
    () => buildDistribution(predictions.map((row) => row.Predicted_Revenue)),
    [predictions]
  );

  const enhancedRows = useMemo(() => {
    const total = predictedRevenueTotal || 1;
    return predictionsWithError.map((row) => {
      const predictionPct = (row.Predicted_Revenue / total) * 100;
      const accuracyPct = row.Revenue != null
        ? Math.max(0, 100 - (Math.abs(row.error) / Math.abs(row.Revenue)) * 100)
        : null;
      return { ...row, predictionPct, accuracyPct, variance: row.error };
    });
  }, [predictionsWithError, predictedRevenueTotal]);

  const filteredSortedRows = useMemo(() => {
    let rows = enhancedRows;
    if (tableSearch.trim()) {
      const q = tableSearch.trim().toLowerCase();
      rows = rows.filter((r) => formatDate(r.Order_Date).toLowerCase().includes(q));
    }
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
  }, [enhancedRows, tableSearch, sortKey, sortDir]);

  const toggleTableSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const recommendations = useMemo(() => {
    if (!metrics || !health || !trend) return [];
    const recs = [];
    recs.push(metrics.R2 >= 0.8 ? "Model accuracy is strong enough to support short-term inventory and staffing decisions." : "Model accuracy is moderate — validate forecasts against other signals before acting on them.");
    recs.push(highVarianceDays.length > 0 ? `Monitor the ${highVarianceDays.length} historical day${highVarianceDays.length > 1 ? "s" : ""} with unusually high prediction error.` : "Prediction error is consistent across the evaluation period — no unusually volatile days detected.");
    recs.push(overallBias > 0 ? "The model tends to under-predict revenue — build in a small planning buffer above the raw forecast." : overallBias < 0 ? "The model tends to over-predict revenue — apply a conservative discount before using forecasts for commitments." : "The model shows no consistent over- or under-prediction bias.");
    return recs;
  }, [metrics, health, trend, highVarianceDays, overallBias]);

  const nextSteps = useMemo(() => {
    if (!metrics) return [];
    const steps = [];
    steps.push(healthTier === "Low" || healthTier === "Medium" ? "Consider retraining with a longer training window to improve R²." : "Current training window is producing reliable results — maintain the existing retraining cadence.");
    steps.push(`Re-evaluate the model after the next ${metrics.test_days ?? "upcoming"}-day test window to confirm accuracy holds.`);
    if (highVarianceDays.length > 0) steps.push("Investigate the flagged high-variance historical dates for any recurring calendar or demand pattern.");
    return steps;
  }, [metrics, healthTier, highVarianceDays]);

  const explanations = useMemo(() => {
    if (!metrics || !health || !trend) return [];
    const expls = [];
    expls.push(`Revenue is projected to peak around ${formatDate(trend.peakDate)} at ${formatCurrency(trend.peakValue)}, based on the trained model's demand pattern for that period.`);
    expls.push(metrics.R2 >= 0.8 ? `Confidence is ${health.reliability.toLowerCase()} because the model explains ${(metrics.R2 * 100).toFixed(0)}% of historical revenue variance (R² = ${metrics.R2.toFixed(2)}).` : `Confidence is ${health.reliability.toLowerCase()} because the model only explains ${(metrics.R2 * 100).toFixed(0)}% of historical revenue variance (R² = ${metrics.R2.toFixed(2)}) — treat projections cautiously.`);
    expls.push(trend.direction === "Increasing" ? `The business should prepare for rising demand — expected growth of ${trend.growthPct}% across the forecast window.` : trend.direction === "Declining" ? `The business should prepare for softening demand — an expected decline of ${Math.abs(trend.growthPct)}% across the forecast window.` : "The business should expect relatively flat demand across the forecast window, with no strong directional signal.");
    expls.push(highVarianceDays.length > 0 ? `${highVarianceDays.length} historical day${highVarianceDays.length > 1 ? "s" : ""} — including ${formatDate(worstForecastDay?.Order_Date)} — showed prediction errors well above average and deserve closer attention before planning around similar future dates.` : "No specific dates stand out as high-risk — prediction error was evenly distributed across the evaluation window.");
    return expls;
  }, [metrics, health, trend, highVarianceDays, worstForecastDay]);

  const handleExportCsv = useCallback(() => {
    if (!metrics) return;
    const lines = [
      "Section,Field,Value",
      `Summary,Forecast Period,"${forecastPeriod}"`,
      `Summary,Expected Trend,${trend?.direction ?? ""}`,
      `Summary,Expected Growth %,${trend?.growthPct ?? ""}`,
      `Summary,Model Confidence,${health?.reliability ?? ""}`,
      `Metrics,MAE,${metrics.MAE}`,
      `Metrics,RMSE,${metrics.RMSE}`,
      `Metrics,R2,${metrics.R2}`,
      `Metrics,Training Days,${metrics.train_days}`,
      `Metrics,Testing Days,${metrics.test_days}`,
      `Statistics,Average Absolute Error,${avgAbsError.toFixed(2)}`,
      `Statistics,Overall Bias,${overallBias.toFixed(2)}`,
      `Statistics,High Variance Days,${highVarianceDays.length}`,
      "",
      "Forecast",
      "Date,Historical Revenue,Predicted Revenue,Prediction Error,Prediction %,Accuracy %"
    ];
    enhancedRows.forEach((row) => {
      lines.push([
        formatDate(row.Order_Date),
        row.Revenue != null ? row.Revenue : "",
        row.Predicted_Revenue,
        row.error != null ? row.error.toFixed(2) : "",
        row.predictionPct.toFixed(2),
        row.accuracyPct != null ? row.accuracyPct.toFixed(2) : ""
      ].join(","));
    });
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "forecast-export.csv";
    link.click();
    URL.revokeObjectURL(url);
  }, [metrics, forecastPeriod, trend, health, avgAbsError, overallBias, highVarianceDays, enhancedRows]);

  const handleExportPdf = useCallback(async () => {
    if (!metrics) return;
    try {
      const { jsPDF } = await import("jspdf");
      const autoTable = (await import("jspdf-autotable")).default;
      const doc = new jsPDF();
      let y = 16;
      doc.setFontSize(16);
      doc.text("Sales Forecasting Report", 14, y);
      y += 8;
      doc.setFontSize(10);
      doc.text(`Forecast Period: ${forecastPeriod}`, 14, y);
      y += 6;
      doc.text(`Model Health: ${health?.label ?? "—"} (R2 = ${metrics.R2.toFixed(2)})`, 14, y);
      y += 6;
      doc.text(`Expected Trend: ${trend?.direction ?? "—"} (${trend?.growthPct ?? 0}% growth)`, 14, y);
      y += 10;
      autoTable(doc, {
        startY: y,
        head: [["Metric", "Value"]],
        body: [
          ["MAE", formatNumber(metrics.MAE)],
          ["RMSE", formatNumber(metrics.RMSE)],
          ["R2 Score", metrics.R2.toFixed(2)],
          ["Training Days", metrics.train_days],
          ["Testing Days", metrics.test_days],
        ],
      });
      y += 45;
      doc.setFontSize(12);
      doc.text("Business Recommendations", 14, y);
      y += 6;
      doc.setFontSize(10);
      recommendations.forEach((rec) => {
        const wrapped = doc.splitTextToSize(`• ${rec}`, 180);
        doc.text(wrapped, 14, y);
        y += wrapped.length * 5;
      });
      y += 6;
      autoTable(doc, {
        startY: y,
        head: [["Date", "Actual", "Predicted", "Error", "Accuracy %"]],
        body: enhancedRows.slice(0, 40).map((r) => [
          formatDate(r.Order_Date),
          r.Revenue != null ? formatCurrency(r.Revenue) : "—",
          formatCurrency(r.Predicted_Revenue),
          r.error != null ? formatSignedCurrency(r.error) : "—",
          r.accuracyPct != null ? `${r.accuracyPct.toFixed(1)}%` : "—",
        ]),
      });
      doc.save("forecast-report.pdf");
    } catch (err) {
      console.error(err);
      alert("PDF export requires the 'jspdf' and 'jspdf-autotable' packages. Please run: npm install jspdf jspdf-autotable");
    }
  }, [metrics, forecastPeriod, health, trend, recommendations, enhancedRows]);

  if (loading) {
    return (
      <div className="fx-page fx-fade-in">
        <header className="fx-hero">
          <span className="fx-eyebrow"><Sparkles size={14} /> Machine Learning Forecasting Workspace</span>
          <h1>Sales Forecasting</h1>
          <p>Predict future business performance and evaluate model reliability.</p>
        </header>
        <div className="fx-skeleton-strip">
          <div className="fx-skeleton-card"></div><div className="fx-skeleton-card"></div><div className="fx-skeleton-card"></div><div className="fx-skeleton-card"></div>
        </div>
        <div className="fx-panel fx-skeleton-chart"></div>
      </div>
    );
  }

  return (
    <div className="fx-page fx-fade-in">
      <header className="fx-hero">
        <span className="fx-eyebrow">
          <Sparkles size={14} />
          Machine Learning Forecasting Workspace
        </span>
        <h1>Sales Forecasting</h1>
        <p>Predict future business performance and evaluate model reliability using historical revenue data.</p>
      </header>

      {error && (
        <div className="error-message" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
          <span>{error}</span>
          <button onClick={loadForecast} className="fx-retry-btn">
            <RefreshCw size={14} /> Retry
          </button>
        </div>
      )}

      {!error && metrics && (
        <>
          {/* FORECAST CONTROL PANEL */}
          <section className="fx-panel fx-controls">
            <div className="fx-section-header">
              <span className="fx-eyebrow"><SlidersHorizontal size={14} /> Forecast Controls</span>
              <h2>Configure This Forecast</h2>
            </div>
            <div className="fx-controls-grid">
              <div className="fx-control-group">
                <label>Forecast Horizon</label>
                <div className="fx-pill-group">
                  {HORIZON_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      className={`fx-pill ${horizon === opt.value ? "fx-pill-active" : ""}`}
                      onClick={() => setHorizon(opt.value)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                {horizon === "custom" && (
                  <div style={{ marginTop: 8 }}>
                    <label htmlFor="fx-custom-date">Forecast Until</label>
                    <input id="fx-custom-date" type="date" value={customDate} onChange={(e) => setCustomDate(e.target.value)} className="fx-date-input" />
                  </div>
                )}
                <p className="fx-control-note">
                    <Info size={12} /> Forecast updates automatically when the horizon changes.
                </p>
              </div>
              <div className="fx-control-group">
                <label>Region</label>
                <select className="fx-select" value={regionFilter} onChange={e => setRegionFilter(e.target.value)}>
                  <option value="All">All Regions</option>
                  {availableRegions.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <div className="fx-control-group">
                <label>Category</label>
                <select className="fx-select" value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
                  <option value="All">All Categories</option>
                  {availableCategories.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
          </section>

          {/* FORECAST KPIs */}
          <section className="fx-kpi-strip">
            <div className="fx-kpi-card">
              <div className="fx-kpi-icon"><TrendingUp size={20} /></div>
              <span className="fx-kpi-label">Predicted Revenue</span>
              <strong className="fx-kpi-value">{formatCurrency(predictedRevenueTotal)}</strong>
              <span className="fx-kpi-sub">Sum across forecast period</span>
            </div>
            <div className="fx-kpi-card">
              <div className="fx-kpi-icon"><Target size={20} /></div>
              <span className="fx-kpi-label">Forecast Period</span>
              <strong className="fx-kpi-value fx-kpi-value-sm">{forecastPeriod}</strong>
              <span className="fx-kpi-sub">Evaluation & Future window</span>
            </div>
            <div className="fx-kpi-card">
              <div className="fx-kpi-icon"><Activity size={20} /></div>
              <span className="fx-kpi-label">Model Accuracy (R²)</span>
              <strong className="fx-kpi-value">{metrics.R2.toFixed(2)}</strong>
              <span className="fx-kpi-sub">Goodness of historical fit</span>
            </div>
            <div className="fx-kpi-card">
              <div className="fx-kpi-icon"><Gauge size={20} /></div>
              <span className="fx-kpi-label">RMSE</span>
              <strong className="fx-kpi-value">{formatNumber(metrics.RMSE)}</strong>
              <span className="fx-kpi-sub">Root mean squared error</span>
            </div>
          </section>

          {/* FORECAST SUMMARY */}
          {trend && (
            <section className="fx-panel">
              <div className="fx-section-header">
                <span className="fx-eyebrow">Forecast Summary</span>
                <h2>At a Glance</h2>
              </div>
              <div className="fx-summary-grid">
                <div className="fx-summary-item">
                  <span>Expected Trend</span>
                  <strong style={{ color: TREND_COLOR[trend.direction] }}>
                    <TrendIcon size={16} style={{ verticalAlign: "-3px", marginRight: 4 }} />
                    {trend.direction}
                  </strong>
                </div>
                <div className="fx-summary-item">
                  <span>Peak Forecast Period</span>
                  <strong>{formatDate(trend.peakDate)}</strong>
                  <small>{formatCurrency(trend.peakValue)}</small>
                </div>
                <div className="fx-summary-item">
                  <span>Lowest Forecast Period</span>
                  <strong>{formatDate(trend.lowDate)}</strong>
                  <small>{formatCurrency(trend.lowValue)}</small>
                </div>
                <div className="fx-summary-item">
                  <span>Average Forecast</span>
                  <strong>{formatCurrency(trend.avgDaily)}</strong>
                </div>
                <div className="fx-summary-item">
                  <span>Forecast Confidence</span>
                  <strong>{health.reliability}</strong>
                </div>
                <div className="fx-summary-item fx-summary-wide">
                  <span>Forecast Recommendation</span>
                  <strong className="fx-summary-text">{recommendations[0]}</strong>
                </div>
              </div>
            </section>
          )}

          {/* CHART AREA */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow">Forecast Overview</span>
              <h2>Revenue: Historical vs. Predicted</h2>
            </div>
            {trend && (
              <div className="fx-trend-strip">
                <span className="fx-trend-badge" style={{ color: TREND_COLOR[trend.direction], background: TREND_COLOR[trend.direction]+"15" }}>
                  <TrendIcon size={18} /> {trend.direction}
                </span>
                <span className="fx-trend-metric">Expected Growth: <strong>{trend.growthPct}%</strong></span>
                <span className="fx-trend-metric">Peak Date: <strong>{formatDate(trend.peakDate)}</strong></span>
                <span className="fx-trend-metric">Avg. Daily Forecast: <strong>{formatCurrency(trend.avgDaily)}</strong></span>
              </div>
            )}
            <div className="fx-chart-controls">
              <label className="fx-checkbox"><input type="checkbox" checked={showHistorical} onChange={(e) => setShowHistorical(e.target.checked)} /> Show Historical</label>
              <label className="fx-checkbox"><input type="checkbox" checked={showForecastLine} onChange={(e) => setShowForecastLine(e.target.checked)} /> Show Forecast</label>
              <label className="fx-checkbox"><input type="checkbox" checked={showConfidenceBand} onChange={(e) => setShowConfidenceBand(e.target.checked)} /> Show Confidence Band</label>
              <div className="fx-pill-group" style={{ marginLeft: "auto" }}>
                {["worst", "expected", "best"].map((s) => (
                  <button key={s} className={`fx-pill ${scenario === s ? "fx-pill-active" : ""}`} onClick={() => setScenario(s)}>
                    {s === "worst" ? "Worst Case" : s === "best" ? "Best Case" : "Expected"}
                  </button>
                ))}
              </div>
            </div>
            {chartData.length > 0 ? (
              <div className="fx-chart-lg">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="Order_Date" tickFormatter={formatDate} tick={{ fontSize: 12 }} />
                    <YAxis tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} tick={{ fontSize: 12 }} />
                    <Tooltip
                      labelFormatter={formatDate}
                      formatter={(value, name) => {
                        if (Array.isArray(value)) {
                          return [
                            `${formatCurrency(value[0])} - ${formatCurrency(value[1])}`,
                            name,
                          ];
                        }
                        return [formatCurrency(value), name];
                      }}
                    />
                    <Legend />
                    {showConfidenceBand && <Area type="monotone" dataKey="confidenceBand" name="Confidence Band (± MAE)" stroke="none" fill="#a78bfa" fillOpacity={0.18} />}
                    {showHistorical && <Line type="monotone" dataKey="Revenue" name="Historical Revenue" stroke="#4f46e5" strokeWidth={3} dot={false} connectNulls={false} />}
                    {showForecastLine && <Line type="monotone" dataKey="scenarioValue" name={`Predicted Revenue (${scenario === "best" ? "Best Case" : scenario === "worst" ? "Worst Case" : "Expected"})`} stroke="#a78bfa" strokeWidth={3} strokeDasharray="6 4" dot={false} />}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state">
                <LineChartIcon size={28} />
                <h4>No forecast data available</h4>
                <p>The forecast evaluation endpoint returned no predictions.</p>
              </div>
            )}
          </section>

          {/* INSIGHTS */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow">Forecast Insights</span>
              <h2>Key Numbers From This Forecast</h2>
            </div>
            <div className="fx-insights-grid">
              <div className="fx-insight-card"><span>Highest Predicted Revenue</span><strong>{bestForecastDay ? formatCurrency(bestForecastDay.Predicted_Revenue) : "—"}</strong><small>{bestForecastDay ? formatDate(bestForecastDay.Order_Date) : ""}</small></div>
              <div className="fx-insight-card"><span>Lowest Predicted Revenue</span><strong>{lowestForecastDay ? formatCurrency(lowestForecastDay.Predicted_Revenue) : "—"}</strong><small>{lowestForecastDay ? formatDate(lowestForecastDay.Order_Date) : ""}</small></div>
              <div className="fx-insight-card"><span>Average Predicted Revenue</span><strong>{formatCurrency(averagePredictedRevenue)}</strong><small>Across {predictions.length} forecast days</small></div>
              <div className="fx-insight-card"><span>Forecast Period</span><strong className="fx-insight-value-sm">{forecastPeriod}</strong></div>
              <div className="fx-insight-card"><span>Best Forecast Day</span><strong>{bestForecastDay ? formatDate(bestForecastDay.Order_Date) : "—"}</strong><small>Highest predicted revenue</small></div>
              <div className="fx-insight-card"><span>Worst Forecast Day</span><strong>{worstForecastDay ? formatDate(worstForecastDay.Order_Date) : "—"}</strong><small>Largest prediction error (Historical)</small></div>
            </div>
          </section>

          {/* PREDICTION ACCURACY */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow"><Radar size={14} /> Prediction Accuracy</span>
              <h2>How Close Were The Historical Predictions?</h2>
            </div>
            <div className="fx-accuracy-grid">
              <div className="fx-accuracy-chart">
                <p className="fx-panel-caption">Actual vs. predicted revenue — points closer to the dashed line indicate more accurate historical predictions.</p>
                <ResponsiveContainer width="100%" height={260}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="predicted" name="Predicted" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} tick={{ fontSize: 11 }} />
                    <YAxis type="number" dataKey="actual" name="Actual" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} tick={{ fontSize: 11 }} />
                    <Tooltip content={<ScatterTooltip />} />
                    <ReferenceLine segment={[{ x: scatterMin, y: scatterMin }, { x: scatterMax, y: scatterMax }]} stroke="#9ca3af" strokeDasharray="4 4" />
                    <Scatter data={scatterData} fill="#7c3aed" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <div className="fx-gauge-wrap">
                <p className="fx-panel-caption">Model accuracy (R²)</p>
                <ResponsiveContainer width="100%" height={180}>
                  <RadialBarChart innerRadius="70%" outerRadius="100%" data={[{ name: "R2", value: metrics.R2 * 100, fill: health.color }]} startAngle={180} endAngle={0}>
                    <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                    <RadialBar background dataKey="value" cornerRadius={8} />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="fx-gauge-value">
                  <strong>{metrics.R2.toFixed(2)}</strong>
                  <span>{health.label}</span>
                </div>
              </div>
            </div>
          </section>

          {/* FORECAST STATISTICS */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow">Forecast Statistics</span>
              <h2>Model Evaluation Metrics</h2>
            </div>
            <div className="fx-stat-strip">
              <div className="fx-stat-item"><span>MAE</span><strong>{formatNumber(metrics.MAE)}</strong></div>
              <div className="fx-stat-item"><span>RMSE</span><strong>{formatNumber(metrics.RMSE)}</strong></div>
              <div className="fx-stat-item"><span>R² Score</span><strong>{metrics.R2.toFixed(2)}</strong></div>
              <div className="fx-stat-item"><span>Training Days</span><strong>{formatNumber(metrics.train_days)}</strong></div>
              <div className="fx-stat-item"><span>Testing Days</span><strong>{formatNumber(metrics.test_days)}</strong></div>
            </div>
          </section>

          {/* ERROR ANALYSIS */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow"><AlertTriangle size={14} /> Error Analysis</span>
              <h2>Prediction Error by Day (Historical)</h2>
            </div>
            <p className="fx-panel-caption">Bars above zero mean the model under-predicted revenue; bars below zero mean it over-predicted. Color reflects magnitude relative to average absolute error ({formatNumber(avgAbsError)}).</p>
            {errorChartData.length > 0 ? (
              <div className="fx-chart-md">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={errorChartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(value) => [formatSignedCurrency(value), "Prediction Error"]} />
                    <ReferenceLine y={0} stroke="#98a2b3" />
                    <Bar dataKey="error" radius={[4, 4, 4, 4]}>
                      {errorChartData.map((row, index) => <Cell key={index} fill={getErrorSeverityColor(Math.abs(row.error), avgAbsError)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state"><AlertTriangle size={28} /><h4>No error data available</h4><p>Prediction error requires at least one historical forecast row.</p></div>
            )}
            {distributionData.length > 0 && (
              <>
                <p className="fx-panel-caption fx-panel-caption-spaced">Distribution of predicted revenue across the forecast period.</p>
                <div className="fx-chart-sm">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distributionData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="range" tick={{ fontSize: 10 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="count" name="Days" fill="#a78bfa" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
          </section>

          {/* FORECAST EXPLANATION */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow"><Lightbulb size={14} /> Forecast Explanation</span>
              <h2>Why The Model Says This</h2>
            </div>
            <ul className="fx-recommendation-list">
              {explanations.map((text, index) => <li key={index}><Info size={16} />{text}</li>)}
            </ul>
          </section>

          {/* DETAILED TABLE */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow"><ClipboardList size={14} /> Detailed Breakdown</span>
              <h2>Historical vs. Predicted</h2>
            </div>
            <div className="fx-table-toolbar">
              <div className="fx-search-wrap">
                <Search size={15} className="fx-search-icon" />
                <input type="text" placeholder="Search by date..." value={tableSearch} onChange={(e) => setTableSearch(e.target.value)} className="fx-search-input" />
              </div>
            </div>
            {filteredSortedRows.length > 0 ? (
              <div className="fx-table-scroll">
                <table className="forecast-table">
                  <thead>
                    <tr>
                      {[{ key: "Order_Date", label: "Date" }, { key: "Revenue", label: "Historical Revenue" }, { key: "Predicted_Revenue", label: "Predicted Revenue" }, { key: "error", label: "Prediction Error" }, { key: "predictionPct", label: "Prediction %" }, { key: "accuracyPct", label: "Accuracy %" }].map((col) => (
                        <th key={col.key} onClick={() => toggleTableSort(col.key)}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>{col.label} <ArrowUpDown size={11} /></span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSortedRows.map((row, index) => (
                      <tr key={row.Order_Date ?? index}>
                        <td>{formatDate(row.Order_Date)}</td>
                        <td>{row.Revenue != null ? formatCurrency(row.Revenue) : "—"}</td>
                        <td>{formatCurrency(row.Predicted_Revenue)}</td>
                        <td className={getErrorSeverityClass(row.error != null ? Math.abs(row.error) : null, avgAbsError)}>
                          {row.error != null ? formatSignedCurrency(row.error) : "—"}
                        </td>
                        <td>{row.predictionPct.toFixed(1)}%</td>
                        <td>{row.accuracyPct != null ? `${row.accuracyPct.toFixed(1)}%` : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state"><ClipboardList size={28} /><h4>No matching rows</h4><p>Try a different search term.</p></div>
            )}
          </section>

          {/* BUSINESS RECOMMENDATIONS */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow"><Lightbulb size={14} /> Business Recommendations</span>
              <h2>What This Means For The Business</h2>
            </div>
            <ul className="fx-recommendation-list">
              {recommendations.map((text, index) => (
                <li key={index}>{overallBias > 0 ? <TrendingUp size={16} /> : overallBias < 0 ? <TrendingDown size={16} /> : <Activity size={16} />}<span>{text}</span></li>
              ))}
            </ul>
          </section>

          {/* MODEL DIAGNOSTICS & NEXT STEPS */}
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow"><HeartPulse size={14} /> Model Diagnostics</span>
              <h2>Model Health</h2>
            </div>
            <div className={`fx-health-card ${health.className}`}>
              <div className="fx-health-badge">{health.label}</div>
              <p className="fx-health-score">R² = {metrics.R2.toFixed(2)}</p>
              <p className="fx-health-reliability">Forecast reliability: {health.reliability}</p>
              <p className="fx-health-note">{health.note}</p>
            </div>
          </section>
          <section className="fx-panel">
            <div className="fx-section-header">
              <span className="fx-eyebrow"><ListChecks size={14} /> Next Steps</span>
              <h2>Next Forecast Recommendations</h2>
            </div>
            <ul className="fx-next-steps">
              {nextSteps.map((text, index) => <li key={index}>{text}</li>)}
            </ul>
          </section>

          {/* MODEL INFO (Expandable) */}
          <section className="fx-panel">
            <button className="fx-expand-toggle" onClick={() => setModelInfoOpen((o) => !o)}>
              <span className="fx-section-header" style={{ margin: 0, border: "none", padding: 0 }}>
                <span className="fx-eyebrow"><Info size={14} /> Model Information</span>
                <h2>Model Details</h2>
              </span>
              {modelInfoOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
            {modelInfoOpen && (
              <div className="fx-model-info-grid">
                <div className="fx-model-info-item"><span>Model Name</span><strong>Revenue Forecasting Model</strong></div>
                <div className="fx-model-info-item"><span>Training Days</span><strong>{formatNumber(metrics.train_days)}</strong></div>
                <div className="fx-model-info-item"><span>Testing Days</span><strong>{formatNumber(metrics.test_days)}</strong></div>
                <div className="fx-model-info-item"><span>Model Accuracy (R²)</span><strong>{metrics.R2.toFixed(2)}</strong></div>
                <div className="fx-model-info-item"><span>Reliability</span><strong>{health.reliability}</strong></div>
                <div className="fx-model-info-item"><span>Version</span><strong>v2.0 (Future Ready)</strong></div>
                <div className="fx-model-info-item fx-model-info-wide"><span>Status</span><strong>Forecast Horizon, Region, and Category controls are now active and retrieving live backend data.</strong></div>
              </div>
            )}
          </section>

          {/* EXPORTS */}
          <section className="export-section fx-export">
            <button className="export-button" onClick={handleExportCsv}><Download size={15} style={{ marginRight: 6 }} /> Download CSV</button>
            <button className="export-button secondary" onClick={handleExportPdf}><FileText size={15} style={{ marginRight: 6 }} /> Export PDF</button>
          </section>
        </>
      )}
    </div>
  );
}

export default Forecasting;