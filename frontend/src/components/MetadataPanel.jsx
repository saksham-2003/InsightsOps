// src/components/MetadataPanel.jsx
import React, { useState } from "react";
import {
  Clock,
  Target,
  Wrench,
  BarChart2,
  TrendingUp,
  Cpu,
  Calendar,
  Database,
  Search,
  ChevronDown,
  ChevronUp,
  Sliders
} from "lucide-react";

const ACCENT = "#6366f1";
const BLUE_DARK = "#0f172a";
const BG_LIGHT = "#f8fafc";
const BORDER = "#e2e8f0";

/**
 * Format tool key or string into a clean readable badge label.
 */
const formatToolName = (toolKey) => {
  if (typeof toolKey !== "string") return String(toolKey);
  return toolKey
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

/**
 * MetadataPanel - A production-ready, collapsible metadata and telemetry display component
 * featuring modern information cards, icons for each field, badge rendering for tool arrays,
 * smooth expand/collapse animations, and missing value fallbacks.
 */
export default function MetadataPanel({ metadata = {} }) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Helper to safely format values or fallback to "Not Available"
  const getDisplayVal = (val, formatter) => {
    if (val === null || val === undefined || val === "" || (Array.isArray(val) && val.length === 0)) {
      return <span style={{ color: '#94a3b8', fontStyle: 'italic', fontWeight: 400 }}>Not Available</span>;
    }
    return formatter ? formatter(val) : val;
  };

  const {
    executionTime,
    confidence,
    toolsUsed,
    evidenceCount,
    chartType,
    model,
    timestamp,
    rowsAnalyzed,
    filtersApplied
  } = metadata;

  return (
    <div className="metadata-panel-wrapper">
      <style>{`
        .metadata-panel-wrapper {
          margin-top: 18px;
          border: 1px solid ${BORDER};
          border-radius: 14px;
          background: ${BG_LIGHT};
          overflow: hidden;
          font-size: 13px;
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
          box-sizing: border-box;
          width: 100%;
        }
        .metadata-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 18px;
          background: #f8fafc;
          cursor: pointer;
          font-weight: 600;
          color: #334155;
          transition: background 0.2s;
          user-select: none;
        }
        .metadata-header:hover {
          background: #f1f5f9;
        }
        .metadata-body {
          padding: 16px 18px;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 14px;
          border-top: 1px solid ${BORDER};
          background: white;
          animation: fadeInMeta 0.25s ease-out forwards;
        }
        @keyframes fadeInMeta {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .metadata-card {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 10px 12px;
          background: ${BG_LIGHT};
          border: 1px solid #f1f5f9;
          border-radius: 10px;
          box-sizing: border-box;
        }
        .metadata-icon-wrap {
          padding: 8px;
          background: white;
          border-radius: 8px;
          color: ${ACCENT};
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 1px 3px rgba(0,0,0,0.04);
          flex-shrink: 0;
        }
        .metadata-content {
          display: flex;
          flex-direction: column;
          gap: 2px;
          overflow: hidden;
          width: 100%;
        }
        .metadata-label {
          color: #64748b;
          font-size: 11px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: 0.04em;
        }
        .metadata-val {
          color: ${BLUE_DARK};
          font-weight: 700;
          font-size: 13.5px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .metadata-badge-container {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-top: 2px;
        }
        .metadata-badge {
          background: #e0e7ff;
          color: ${ACCENT};
          padding: 2px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
          text-transform: capitalize;
        }
      `}</style>

      {/* Requirement 3 & 4: Collapsible Header with smooth toggle state */}
      <div className="metadata-header" onClick={() => setIsExpanded(!isExpanded)} role="button" aria-expanded={isExpanded}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Database size={15} color={ACCENT} /> Execution Telemetry & Evidence Verification
        </span>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </div>

      {/* Collapsible Content Area */}
      {isExpanded && (
        <div className="metadata-body">
          
          {/* 1. Execution Time */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><Clock size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">⏱ Execution Time</span>
              <span className="metadata-val">
                {getDisplayVal(executionTime, (val) => `${val} sec`)}
              </span>
            </div>
          </div>

          {/* 2. Confidence */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><Target size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">🎯 Confidence</span>
              <span className="metadata-val">
                {getDisplayVal(confidence, (val) => `${(Number(val) * 100).toFixed(0)}%`)}
              </span>
            </div>
          </div>

          {/* 3. Tools Used (Requirement 6: Display arrays as badges) */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><Wrench size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">🛠 Tools Used</span>
              <div className="metadata-val">
                {Array.isArray(toolsUsed) && toolsUsed.length > 0 ? (
                  <div className="metadata-badge-container">
                    {toolsUsed.map((tool, i) => (
                      <span key={i} className="metadata-badge">{formatToolName(tool)}</span>
                    ))}
                  </div>
                ) : (
                  getDisplayVal(toolsUsed)
                )}
              </div>
            </div>
          </div>

          {/* 4. Evidence Count */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><BarChart2 size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">📊 Evidence Count</span>
              <span className="metadata-val">
                {getDisplayVal(evidenceCount, (val) => `${val} Points`)}
              </span>
            </div>
          </div>

          {/* 5. Chart Type */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><TrendingUp size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">📈 Chart Type</span>
              <span className="metadata-val" style={{ textTransform: 'capitalize' }}>
                {getDisplayVal(chartType, formatToolName)}
              </span>
            </div>
          </div>

          {/* 6. AI Model */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><Cpu size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">🤖 AI Model</span>
              <span className="metadata-val">
                {getDisplayVal(model)}
              </span>
            </div>
          </div>

          {/* 7. Timestamp */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><Calendar size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">📅 Timestamp</span>
              <span className="metadata-val">
                {getDisplayVal(timestamp, (val) => new Date(val).toLocaleString())}
              </span>
            </div>
          </div>

          {/* 8. Rows Analyzed */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><Database size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">🗂 Rows Analyzed</span>
              <span className="metadata-val">
                {getDisplayVal(rowsAnalyzed, (val) => Number(val).toLocaleString())}
              </span>
            </div>
          </div>

          {/* 9. Filters Applied */}
          <div className="metadata-card">
            <div className="metadata-icon-wrap"><Sliders size={16} /></div>
            <div className="metadata-content">
              <span className="metadata-label">🔍 Filters Applied</span>
              <span className="metadata-val">
                {typeof filtersApplied === 'object' && filtersApplied !== null
                  ? Object.entries(filtersApplied)
                      .filter(([_, v]) => v !== null && v !== undefined && v !== "")
                      .map(([k, v]) => `${k}: ${v}`)
                      .join(", ") || "None"
                  : getDisplayVal(filtersApplied)}
              </span>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}