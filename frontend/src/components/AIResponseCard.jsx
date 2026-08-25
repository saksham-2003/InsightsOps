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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 4 }}>
      {items.map((item, idx) => (
        <div
          key={idx}
          style={{
            display: 'flex',
            gap: 14,
            alignItems: 'flex-start',
            padding: '13px 16px',
            background: '#f8fafc',
            borderRadius: 10,
            border: '1px solid #e2e8f0',
            transition: 'box-shadow 0.2s ease, border-color 0.2s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = '0 4px 14px rgba(99,102,241,0.07)';
            e.currentTarget.style.borderColor = '#c7d2fe';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = 'none';
            e.currentTarget.style.borderColor = '#e2e8f0';
          }}
        >
          <span style={{
            minWidth: 26, height: 26, borderRadius: '50%',
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            color: 'white', fontSize: 11, fontWeight: 800,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            boxShadow: '0 2px 6px rgba(99,102,241,0.25)'
          }}>
            {idx + 1}
          </span>
          <span style={{ fontSize: 14, color: '#1e293b', lineHeight: 1.7, paddingTop: 1 }}>
            {item}
          </span>
        </div>
      ))}
    </div>
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
  // evidence from AIAnalyst.jsx is keyed by tool name ("forecast_evaluation").
  // evidence.Forecast_Metrics / Forecast_Trends only exist in the LLM context
  // object, which is NOT what gets passed here. Always read the tool-result key
  // first so the path is reliable; fall through to context-style keys as a backup.
  const forecastMetrics =
      evidence?.forecast_evaluation?.metrics ||
      evidence?.Forecast_Metrics ||
      {};

  const rawForecastTrends =
      evidence?.forecast_evaluation?.predictions ||   // canonical tool-result path
      evidence?.Forecast_Trends ||                    // context-style (fallback)
      (Array.isArray(evidence) ? evidence : []);

  const forecastTrends = rawForecastTrends.filter(item => {
      const actualRevenue = item?.Revenue ?? item?.revenue;

      return (
          (actualRevenue === null || actualRevenue === undefined) &&
          (item?.Predicted_Revenue !== undefined ||
          item?.predicted_revenue !== undefined)
      );
  });
  console.log("========== FORECAST DEBUG ==========");
  console.log("forecastTrends:", forecastTrends);
  console.log("forecastTrends length:", forecastTrends.length);
  console.log(
    "Predicted records:",
    forecastTrends.filter(
      item =>
        item.Predicted_Revenue !== undefined &&
        item.Predicted_Revenue !== null
    )
  );
  console.log("====================================");

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
          value: Number(
              forecastMetrics.r2_score ?? forecastMetrics.R2
          ).toFixed(2),
          icon: <Activity size={18} color="#f59e0b" />
      });
  }


  // ----------------------------------------------------
  // Forecast KPIs
  // Only use FUTURE forecast rows.
  // Historical rows have an actual Revenue value,
  // while future forecast rows have Revenue = null.
  // ----------------------------------------------------

  if (forecastTrends.length > 0) {

      const predictedValues = forecastTrends
          .map(item =>
              item.Predicted_Revenue ??
              item.predicted_revenue
          )
          .filter(v => v !== undefined && v !== null)
          .map(Number)
          .filter(v => Number.isFinite(v));

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

          kpis.push({
              title: "Forecast Period",
              value: `${forecastTrends.length} Days`,
              icon: <Calendar size={18} color="#6366f1" />
          });
      }
  }

  return kpis;
};

/**
 * Reads Phase B structured_evidence_facts from the evidence payload and
 * returns a trend badge object for the KPI title provided.
 * Returns null if no matching fact or no clear trend direction.
 */
const getTrendBadge = (kpiTitle, evidence) => {
  const facts = evidence?.structured_evidence_facts;
  if (!Array.isArray(facts) || facts.length === 0) return null;

  const titleLower = kpiTitle.toLowerCase().replace(/\s+/g, '');
  const fact = facts.find(f => {
    const metricLower = (f.metric || '').toLowerCase().replace(/\s+/g, '');
    return metricLower.includes(titleLower) || titleLower.includes(metricLower.substring(0, 6));
  });

  if (!fact) return null;

  const trend = fact.trend || '';
  if (trend === 'Increasing' || trend === 'Dominant' || trend === 'Leading')
    return { symbol: '▲', color: '#10b981', bg: '#f0fdf4' };
  if (trend === 'Declining' || trend === 'Lagging' || trend === 'Warning' || trend === 'Elevated')
    return { symbol: '▼', color: '#ef4444', bg: '#fef2f2' };
  if (trend === 'Stable' || trend === 'Current Baseline')
    return { symbol: '—', color: '#64748b', bg: '#f8fafc' };
  return null;
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
                    {availableKpis.map((kpi, idx) => {
                      const badge = getTrendBadge(kpi.title, message.evidence);
                      return (
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
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                            <span style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              {kpi.title}
                            </span>
                            <div style={{ padding: 6, background: '#f8fafc', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              {kpi.icon}
                            </div>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                            <div style={{ fontSize: 20, fontWeight: 800, color: BLUE_DARK, letterSpacing: '-0.02em' }}>
                              {kpi.value}
                            </div>
                            {badge && (
                              <span style={{
                                fontSize: 11, fontWeight: 700, color: badge.color,
                                background: badge.bg, borderRadius: 6,
                                padding: '2px 7px', letterSpacing: '0.02em'
                              }}>
                                {badge.symbol}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Executive Summary Card */}
                {message.content.executive_summary && (
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
                )}

                {/* Embedded Visualization Chart */}
                <div style={{ marginBottom: 24 }}>
                  <AIChartRenderer
                    visualization={message.visualization}
                    evidenceData={message.evidence}
                  />
                </div>

                {/* Section divider — only shown when content sections follow */}
                {(message.content.key_findings?.length > 0 ||
                  message.content.business_insights?.length > 0 ||
                  message.content.recommendations?.length > 0 ||
                  message.content.potential_risks?.length > 0) && (
                  <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '8px 0 24px' }} />
                )}

                {/* Key Findings — conditional */}
                {message.content.key_findings?.length > 0 && (
                  <SectionCard icon="🔍" title="Key Findings" color="#1e293b">
                    {renderList(message.content.key_findings)}
                  </SectionCard>
                )}

                {/* Business Insights — conditional */}
                {message.content.business_insights?.length > 0 && (
                  <SectionCard icon="💡" title="Business Insights" color="#312e81">
                    {renderList(message.content.business_insights)}
                  </SectionCard>
                )}

                {/* Recommendations — conditional */}
                {message.content.recommendations?.length > 0 && (
                  <SectionCard icon="🚀" title="Strategic Recommendations" color="#047857">
                    {renderList(message.content.recommendations)}
                  </SectionCard>
                )}

                {/* Potential Risks — conditional */}
                {message.content.potential_risks?.length > 0 && (
                  <SectionCard icon="⚠️" title="Potential Risks & Caveats" color="#b91c1c">
                    {renderList(message.content.potential_risks)}
                  </SectionCard>
                )}

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