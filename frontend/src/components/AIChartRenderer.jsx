// src/components/AIChartRenderer.jsx
import React, { useState } from "react";
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ComposedChart,
  Line,
  AreaChart,
  Area,
  Legend,
  ReferenceLine
} from "recharts";
import { BarChart3, AlertCircle, Loader2 } from "lucide-react";

// Re-use existing chart components
import RevenueChart from "./RevenueChart";
import RegionChart from "./RegionChart";
import CategoryChart from "./CategoryChart";

const ACCENT = "#6366f1";
const BLUE_DARK = "#0f172a";
const BG_LIGHT = "#f8fafc";
const BORDER = "#e2e8f0";

// Enhanced formatting utilities for currency, commas, and axis compacting
const formatCurrency = (v) => `$${(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const formatNumberWithCommas = (v) => (v || 0).toLocaleString();
const compactAxisNumber = (v) => {
  if (v >= 1000000) return `$${(v / 1000000).toFixed(1)}M`;
  if (v >= 1000) return `$${(v / 1000).toFixed(0)}k`;
  return `$${v}`;
};

/**
 * Custom Professional Tooltip Component for cohesive styling across Recharts.
 */
const CustomTooltip = ({ active, payload, label, customLabelName }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: '#0f172a',
        color: '#fff',
        padding: '12px 16px',
        borderRadius: '8px',
        fontSize: '12.5px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        {label && <p style={{ fontWeight: 700, marginBottom: 8, borderBottom: '1px solid rgba(255,255,255,0.15)', paddingBottom: 4 }}>{label}</p>}
        {payload.map((entry, index) => {
          if (entry.value === null || entry.value === undefined) return null;
          const name = customLabelName || entry.name || entry.dataKey;
          const formattedVal = typeof entry.value === 'number' && entry.value > 999 
            ? formatCurrency(entry.value) 
            : entry.value;
          return (
            <div key={index} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, marginBottom: 4 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: entry.color || ACCENT, display: 'inline-block' }}></span>
                {name}:
              </span>
              <span style={{ fontWeight: 600, color: '#fff', marginLeft: 'auto' }}>{formattedVal}</span>
            </div>
          );
        })}
      </div>
    );
  }
  return null;
};

/**
 * Reusable Professional Empty State Card
 */
const EmptyStateCard = ({ title }) => (
  <div style={{ 
    padding: '40px 20px', 
    textAlign: 'center', 
    background: BG_LIGHT, 
    border: `1px solid ${BORDER}`, 
    borderRadius: 12, 
    marginTop: 16, 
    color: '#64748b',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8
  }}>
    <AlertCircle size={28} color="#94a3b8" style={{ opacity: 0.8 }} />
    <div style={{ fontSize: 14, fontWeight: 600, color: '#334155' }}>No data available for {title || 'this chart'}</div>
    <div style={{ fontSize: 12, color: '#94a3b8' }}>Try refining your query or check available metrics.</div>
  </div>
);

/**
 * AIChartRenderer - Enterprise BI Dashboard Grade Visualizer with animations, interactive highlights, and robust formatting.
 */
export default function AIChartRenderer({ visualization, evidenceData }) {
  const [activeBarIndex, setActiveBarIndex] = useState(null);
  const [hoveredLineKey, setHoveredLineKey] = useState(null);

  // If no visualization spec is available, gracefully return null
  if (!visualization || !visualization.type) {
    return null;
  }
  
  const { type, title, x, y, labels, values, actual, predicted, points } = visualization;

  // 1. Horizontal Bar Chart (bottom_products, top_products)
  if (type === "horizontal_bar" && x && y) {
    if (x.length === 0 || y.length === 0) return <EmptyStateCard title={title} />;
    const focus = visualization.focus;

    const chartData = x.map((label, idx) => ({
      Product: label,
      Revenue: y[idx],
      isFocused: focus?.value === label
    }));

    return (
      <div className="aia-chart-box" style={{ width: "100%", height: 380, marginTop: 16, background: '#fff', padding: '12px', borderRadius: '12px', border: `1px solid ${BORDER}` }}>
        {title && <h4 style={{ marginBottom: 12, color: BLUE_DARK, fontSize: 15, fontWeight: 700 }}>{title}</h4>}
        <ResponsiveContainer width="100%" height="88%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={BORDER} />
            <XAxis type="number" tickFormatter={compactAxisNumber} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis dataKey="Product" type="category" width={130} tick={{ fontSize: 11, fill: '#334155', fontWeight: 600 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip customLabelName="Revenue" />} />
            <Bar
              dataKey="Revenue"
              radius={[0, 6, 6, 0]}
              isAnimationActive={true}
              animationDuration={1000}
              onMouseEnter={(_, index) => setActiveBarIndex(index)}
              onMouseLeave={() => setActiveBarIndex(null)}
            >
              {chartData.map((entry, index) => {
                const isHovered = activeBarIndex === index;
                const isFocused = entry.isFocused;
                let fillColor = isFocused ? "#ef4444" : ACCENT;
                let barOpacity = isFocused ? 1 : 0.85;

                // Fade non-hovered elements if a bar is hovered
                if (activeBarIndex !== null && !isHovered) {
                  barOpacity = 0.3;
                }

                return (
                  <Cell
                    key={index}
                    fill={fillColor}
                    opacity={barOpacity}
                    style={{ transition: 'all 0.3s ease', cursor: 'pointer' }}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // 2. Line Chart (monthly_trend) -> Reuse RevenueChart component structure or pattern
  if (type === "line" && x && y) {
    if (x.length === 0 || y.length === 0) return <EmptyStateCard title={title} />;
    const chartData = x.map((label, idx) => ({
      Order_Date: label,
      Revenue: y[idx]
    }));
    return (
      <div style={{ marginTop: 16 }}>
        {title && <h4 style={{ marginBottom: 8, color: BLUE_DARK, fontSize: 15, fontWeight: 700 }}>{title}</h4>}
        <RevenueChart data={chartData} />
      </div>
    );
  }

  // 3. Bar Chart (regional_performance) -> Reuse RegionChart component
  if (type === "bar" && x && y) {
    if (x.length === 0 || y.length === 0) return <EmptyStateCard title={title} />;
    const chartData = x.map((label, idx) => ({
      Region: label,
      Revenue: y[idx]
    }));
    return (
      <div style={{ marginTop: 16 }}>
        {title && <h4 style={{ marginBottom: 8, color: BLUE_DARK, fontSize: 15, fontWeight: 700 }}>{title}</h4>}
        <RegionChart data={chartData} />
      </div>
    );
  }

  // 4. Pie / Category Chart (category_performance) -> Reuse CategoryChart component
  if (type === "pie" && labels && values) {
    if (labels.length === 0 || values.length === 0) return <EmptyStateCard title={title} />;
    const chartData = labels.map((label, idx) => ({
      Category: label,
      Revenue: values[idx]
    }));
    return (
      <div style={{ marginTop: 16 }}>
        {title && <h4 style={{ marginBottom: 8, color: BLUE_DARK, fontSize: 15, fontWeight: 700 }}>{title}</h4>}
        <CategoryChart data={chartData} />
      </div>
    );
  }

  // 5. Multi-Line Chart (forecast)
  if (type === "multi_line" && x) {
    if (x.length === 0) return <EmptyStateCard title={title} />;
    const chartData = x.map((label, idx) => ({
      Order_Date: label,
      Actual_Revenue: actual ? actual[idx] : null,
      Predicted_Revenue: predicted ? predicted[idx] : null
    }));

    return (
      <div className="aia-chart-box" style={{ width: "100%", height: 380, marginTop: 16, background: '#fff', padding: '12px', borderRadius: '12px', border: `1px solid ${BORDER}` }}>
        {title && <h4 style={{ marginBottom: 12, color: BLUE_DARK, fontSize: 15, fontWeight: 700 }}>{title}</h4>}
        <ResponsiveContainer width="100%" height="88%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={BORDER} />
            <XAxis dataKey="Order_Date" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis tickFormatter={compactAxisNumber} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: 12, paddingTop: 8, cursor: 'pointer' }} 
              onMouseEnter={(e) => setHoveredLineKey(e.dataKey)}
              onMouseLeave={() => setHoveredLineKey(null)}
            />
            <Line 
              type="monotone" 
              dataKey="Actual_Revenue" 
              name="Actual Revenue" 
              stroke={BLUE_DARK} 
              strokeWidth={hoveredLineKey && hoveredLineKey !== "Actual_Revenue" ? 1 : 2.5} 
              strokeOpacity={hoveredLineKey && hoveredLineKey !== "Actual_Revenue" ? 0.25 : 1}
              dot={false} 
              isAnimationActive={true}
              animationDuration={1200}
            />
            <Line 
              type="monotone" 
              dataKey="Predicted_Revenue" 
              name="Predicted Revenue" 
              stroke={ACCENT} 
              strokeWidth={hoveredLineKey && hoveredLineKey !== "Predicted_Revenue" ? 1 : 2.5} 
              strokeOpacity={hoveredLineKey && hoveredLineKey !== "Predicted_Revenue" ? 0.25 : 1}
              strokeDasharray="5 5" 
              dot={false} 
              isAnimationActive={true}
              animationDuration={1200}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // 6. Scatter Plot (anomaly_detection)
  if (type === "scatter" && points) {
    if (points.length === 0) return <EmptyStateCard title={title} />;
    return (
      <div className="aia-chart-box" style={{ width: "100%", height: 380, marginTop: 16, background: '#fff', padding: '12px', borderRadius: '12px', border: `1px solid ${BORDER}` }}>
        {title && <h4 style={{ marginBottom: 12, color: BLUE_DARK, fontSize: 15, fontWeight: 700 }}>{title}</h4>}
        <ResponsiveContainer width="100%" height="88%">
          <ScatterChart margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={BORDER} />
            <XAxis type="number" dataKey="x" name="Revenue" tickFormatter={compactAxisNumber} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis type="number" dataKey="y" name="Profit" tickFormatter={compactAxisNumber} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter 
              data={points} 
              fill="#ef4444" 
              isAnimationActive={true}
              animationDuration={1000}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
}