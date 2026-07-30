// src/components/AIResponseCard.jsx
import React, { useState } from "react";
import {
  Copy,
  CheckCircle2,
  ArrowRight,
  Database,
  Wrench,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Activity,
  Cpu,
  Layers,
  Clock,
  DollarSign,
  TrendingUp,
  Percent,
  ShoppingCart,
  Calendar,
  BarChart2,
  Award
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import AIChartRenderer from "./AIChartRenderer";

const BLUE_DARK = "#0f172a";
const BLUE_LIGHT = "#312e81";
const ACCENT = "#6366f1";
const BG_LIGHT = "#f8fafc";
const BORDER = "#e2e8f0";

const formatCurrency = (v) => `$${(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const renderList = (items) => {
  if (!Array.isArray(items) || items.length === 0) return null;

  return (
    <ul style={{ paddingLeft: 22, marginTop: 8, color: '#334155', lineHeight: '1.6' }}>
      {items.map((item, idx) => (
        <li key={idx} style={{ marginBottom: 8 }}>
          {item}
        </li>
      ))}
    </ul>
  );
};

const formatToolName = (toolKey) => {
  return toolKey
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

function SectionCard({ icon, title, children, color = "#312e81" }) {
  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: 14,
        padding: "20px 22px",
        marginBottom: 20,
        boxShadow: "0 2px 10px rgba(15, 23, 42, 0.03)"
      }}
    >
      <h3
        style={{
          marginTop: 0,
          marginBottom: 16,
          color,
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontSize: 17,
          fontWeight: 700,
          borderBottom: "1px solid #f1f5f9",
          paddingBottom: 10
        }}
      >
        <span>{icon}</span>
        {title}
      </h3>

      {children}
    </div>
  );
}

/**
 * Extracts available KPIs dynamically from the evidence payload or tool responses.
 */
const extractKpis = (evidence) => {
  if (!evidence) return [];
  
  const kpis = [];
  
  // Unpack different possible structures in evidence
  const kpiData = evidence.kpi_summary || evidence.KPIs || evidence.kpis || {};
  const forecastMetrics = evidence.Forecast_Metrics || evidence.forecast_evaluation?.metrics || {};
  const forecastTrends = evidence.Forecast_Trends || evidence.forecast_evaluation?.predictions || [];

  const totalRev = kpiData.total_revenue ?? kpiData.Revenue;
  if (totalRev !== undefined && totalRev !== null) {
    kpis.push({
      title: "Total Revenue",
      value: formatCurrency(totalRev),
      icon: <DollarSign size={18} color="#6366f1" />
    });
  }

  const totalProf = kpiData.total_profit ?? kpiData.Profit;
  if (totalProf !== undefined && totalProf !== null) {
    kpis.push({
      title: "Total Profit",
      value: formatCurrency(totalProf),
      icon: <TrendingUp size={18} color="#10b981" />
    });
  }

  const profMargin = kpiData.profit_margin ?? kpiData.Margin;
  if (profMargin !== undefined && profMargin !== null) {
    kpis.push({
      title: "Profit Margin",
      value: `${Number(profMargin).toFixed(1)}%`,
      icon: <Percent size={18} color="#0ea5e9" />
    });
  }

  const totalOrders = kpiData.total_orders ?? kpiData.Orders;
  if (totalOrders !== undefined && totalOrders !== null) {
    kpis.push({
      title: "Total Orders",
      value: Number(totalOrders).toLocaleString(),
      icon: <ShoppingCart size={18} color="#8b5cf6" />
    });
  }

  // Forecast-specific KPIs
  if (forecastMetrics.r2_score !== undefined || forecastMetrics.R2 !== undefined) {
    kpis.push({
      title: "R² Score",
      value: Number(forecastMetrics.r2_score ?? forecastMetrics.R2).toFixed(2),
      icon: <Activity size={18} color="#f59e0b" />
    });
  }

  if (forecastTrends.length > 0) {
    const predictedValues = forecastTrends
      .map(item => item.Predicted_Revenue ?? item.predicted_revenue)
      .filter(v => v !== undefined && v !== null);

    if (predictedValues.length > 0) {
      const maxForecast = Math.max(...predictedValues);
      const minForecast = Math.min(...predictedValues);
      
      kpis.push({
        title: "Highest Forecast",
        value: formatCurrency(maxForecast),
        icon: <Award size={18} color="#10b981" />
      });

      kpis.push({
        title: "Lowest Forecast",
        value: formatCurrency(minForecast),
        icon: <BarChart2 size={18} color="#ef4444" />
      });
    }

    kpis.push({
      title: "Forecast Period",
      value: `${forecastTrends.length} Days`,
      icon: <Calendar size={18} color="#6366f1" />
    });
  }

  return kpis;
};

export default function AIResponseCard({ message, onSelectFollowUp }) {
  const [collapsedMeta, setCollapsedMeta] = useState(true);
  const [copied, setCopied] = useState(false);

  if (!message) return null;

  const handleCopy = () => {
    const textToCopy = typeof message.content === "string" 
      ? message.content 
      : message.content?.executive_summary || "";
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const availableKpis = extractKpis(message.evidence);

  return (
    <div className="aia-bubble ai" style={{ width: '100%', boxSizing: 'border-box' }}>
      
      {/* 1. Tool Badges */}
      {message.toolsUsed && message.toolsUsed.length > 0 && (
        <div style={{ marginBottom: 18, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {message.toolsUsed.map((t, i) => (
            <span key={i} className="aia-tool-badge" style={{
              display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 12px',
              background: 'linear-gradient(135deg, #f8fafc, #f1f5f9)', border: '1px solid #cbd5e1',
              borderRadius: 20, fontSize: 11.5, fontWeight: 700, color: '#334155', textTransform: 'capitalize',
              boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
            }}>
              <Wrench size={12} color={ACCENT} /> {formatToolName(t)}
            </span>
          ))}
        </div>
      )}

      {/* 2. AI Response Content & Layout */}
      {message.content && (
        <div className="aia-section" style={{ marginBottom: 16 }}>
          <div className="markdown-body">

            {typeof message.content === "string" ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            ) : (
              <div>
                
                {/* 3. KPI Summary Section (Rendered above executive summary if metrics exist) */}
                {availableKpis.length > 0 && (
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', 
                    gap: 14, 
                    marginBottom: 24 
                  }}>
                    {availableKpis.map((kpi, idx) => (
                      <div 
                        key={idx} 
                        style={{ 
                          background: '#ffffff', 
                          border: '1px solid #e2e8f0', 
                          borderRadius: 12, 
                          padding: '16px 18px',
                          boxShadow: '0 2px 6px rgba(15, 23, 42, 0.02)',
                          transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                          cursor: 'default'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'translateY(-2px)';
                          e.currentTarget.style.boxShadow = '0 6px 16px rgba(99, 102, 241, 0.08)';
                          e.currentTarget.style.borderColor = '#c7d2fe';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'translateY(0)';
                          e.currentTarget.style.boxShadow = '0 2px 6px rgba(15, 23, 42, 0.02)';
                          e.currentTarget.style.borderColor = '#e2e8f0';
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span style={{ fontSize: 11.5, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            {kpi.title}
                          </span>
                          <div style={{ padding: 6, background: '#f8fafc', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            {kpi.icon}
                          </div>
                        </div>
                        <div style={{ fontSize: 20, fontWeight: 800, color: BLUE_DARK, letterSpacing: '-0.02em' }}>
                          {kpi.value}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Executive Summary Card */}
                <div
                  style={{
                    background: "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)",
                    border: "1px solid #c7d2fe",
                    borderRadius: 14,
                    padding: "20px 24px",
                    marginBottom: 24,
                    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.05)'
                  }}
                >
                  <h2
                    style={{
                      marginTop: 0,
                      marginBottom: 12,
                      color: "#312e81",
                      fontSize: 18,
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8
                    }}
                  >
                    <span>📄</span> Executive Summary
                  </h2>

                  <p
                    style={{
                      margin: 0,
                      lineHeight: 1.8,
                      fontSize: 15,
                      color: '#1e1b4b',
                      fontWeight: 400
                    }}
                  >
                    {message.content.executive_summary}
                  </p>
                </div>
                
                {/* Embedded Visualization Chart */}
                <div style={{ marginBottom: 24 }}>
                  <AIChartRenderer
                    visualization={message.visualization}
                    evidenceData={message.evidence}
                  />
                </div>

                {/* Subtle Section Divider */}
                <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '24px 0' }} />

                {/* Key Findings Section */}
                <SectionCard icon="🔍" title="Key Findings" color="#1e293b">
                  {renderList(message.content.key_findings)}
                </SectionCard>

                {/* Business Insights Section */}
                <SectionCard icon="💡" title="Business Insights" color="#312e81">
                  {renderList(message.content.business_insights)}
                </SectionCard>

                {/* Recommendations Section */}
                <SectionCard icon="🚀" title="Strategic Recommendations" color="#047857">
                  {renderList(message.content.recommendations)}
                </SectionCard>

                {/* Potential Risks Section */}
                <SectionCard icon="⚠️" title="Potential Risks & Caveats" color="#b91c1c">
                  {renderList(message.content.potential_risks)}
                </SectionCard>

              </div>
            )}

          </div>
        </div>
      )}

      {/* 4. Metadata Panel (collapsed by default) */}
      <div className="aia-meta-panel" style={{ marginTop: 24, border: `1px solid ${BORDER}`, borderRadius: 12, background: BG_LIGHT, overflow: 'hidden', fontSize: 13 }}>
        <div className="aia-meta-header" onClick={() => setCollapsedMeta(!collapsedMeta)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 18px', background: '#f8fafc', cursor: 'pointer', fontWeight: 600, color: '#475569' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#334155' }}>
            <Database size={15} color={ACCENT} /> Execution Telemetry & Evidence Verification
          </span>
          {collapsedMeta ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
        </div>
        {!collapsedMeta && (
          <div className="aia-meta-body" style={{ padding: '16px 18px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 14, borderTop: `1px solid ${BORDER}`, background: 'white' }}>
            {message.executionTime !== undefined && message.executionTime !== null && (
              <div className="aia-meta-item" style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ padding: 6, background: BG_LIGHT, borderRadius: 6, color: ACCENT }}><Clock size={14} /></div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ color: '#64748b', fontSize: 10.5, textTransform: 'uppercase', fontWeight: 700 }}>Execution Time</span>
                  <span style={{ color: BLUE_DARK, fontWeight: 700, fontSize: 13.5 }}>{message.executionTime} sec</span>
                </div>
              </div>
            )}
            {message.confidence !== undefined && message.confidence !== null && (
              <div className="aia-meta-item" style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ padding: 6, background: BG_LIGHT, borderRadius: 6, color: ACCENT }}><Activity size={14} /></div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ color: '#64748b', fontSize: 10.5, textTransform: 'uppercase', fontWeight: 700 }}>AI Confidence</span>
                  <span style={{ color: BLUE_DARK, fontWeight: 700, fontSize: 13.5 }}>{(message.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            )}
            {message.toolsUsed && (
              <div className="aia-meta-item" style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ padding: 6, background: BG_LIGHT, borderRadius: 6, color: ACCENT }}><Cpu size={14} /></div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ color: '#64748b', fontSize: 10.5, textTransform: 'uppercase', fontWeight: 700 }}>Tools Used</span>
                  <span style={{ color: BLUE_DARK, fontWeight: 700, fontSize: 13.5 }}>{message.toolsUsed.length > 0 ? message.toolsUsed.map(formatToolName).join(", ") : "None"}</span>
                </div>
              </div>
            )}
            {message.evidenceCount !== undefined && message.evidenceCount !== null && (
              <div className="aia-meta-item" style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ padding: 6, background: BG_LIGHT, borderRadius: 6, color: ACCENT }}><Layers size={14} /></div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ color: '#64748b', fontSize: 10.5, textTransform: 'uppercase', fontWeight: 700 }}>Evidence Count</span>
                  <span style={{ color: BLUE_DARK, fontWeight: 700, fontSize: 13.5 }}>{message.evidenceCount} Points</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 5. Follow-up Questions */}
      {message.followUpQuestions && message.followUpQuestions.length > 0 && (
        <div style={{ marginTop: 22, paddingTop: 16, borderTop: `1px solid ${BORDER}` }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6, letterSpacing: '0.04em' }}>
            <HelpCircle size={14} color={ACCENT} /> Suggested Follow-up Explorations
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {message.followUpQuestions.map((q, idx) => (
              <button
                key={idx}
                className="aia-followup-card"
                onClick={() => onSelectFollowUp && onSelectFollowUp(q)}
                style={{
                  padding: '9px 16px', borderRadius: 10, border: `1px solid ${ACCENT}40`, background: `${ACCENT}08`,
                  color: ACCENT, fontSize: 13, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s',
                  display: 'inline-flex', alignItems: 'center', gap: 6, maxWidth: '100%', boxSizing: 'border-box'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = `${ACCENT}15`;
                  e.currentTarget.style.borderColor = ACCENT;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = `${ACCENT}08`;
                  e.currentTarget.style.borderColor = `${ACCENT}40`;
                }}
              >
                <span>{q}</span> <ArrowRight size={13} style={{ flexShrink: 0 }} />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 6. Copy Button */}
      <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <button
          onClick={handleCopy}
          style={{ background: 'none', border: 'none', color: '#64748b', fontSize: 12.5, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5, padding: '6px 10px', borderRadius: 6, transition: 'background 0.2s' }}
          onMouseEnter={(e) => e.currentTarget.style.background = '#f1f5f9'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
        >
          {copied ? <><CheckCircle2 size={13} color="#10b981" /> Copied to Clipboard</> : <><Copy size={13} /> Copy Response</>}
        </button>
      </div>

    </div>
  );
}