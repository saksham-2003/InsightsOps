import { useState } from "react";
import {
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Brain,
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  RefreshCw,
  MessageSquare,
  Clock,
  Target,
  CheckCircle2,
  FlaskConical,
  Gauge,
  Wrench,
  BarChart3,
  Lightbulb,
  ArrowRight,
} from "lucide-react";

import { queryAIAnalyst, getMonthlyTrend } from "../services/api";

// ----------------------------------------------------------------------
// Scoped identity — deep indigo → violet → pink, distinct from Dashboard
// (indigo/white), Analytics (teal), Forecasting (violet-only), and
// Anomalies (red/orange). Everything is inline + this one <style> block,
// since only this file is in scope for this change.
// ----------------------------------------------------------------------
const INK = "#1e1b2e";
const SUBTEXT = "#6b6580";
const VIOLET = "#7c3aed";
const INDIGO = "#4338ca";
const PINK = "#db2777";
const PANEL_BORDER = "#e9e3fb";
const PANEL_BG = "#faf9ff";

const SUGGESTED_QUESTIONS = [
  "Why was November revenue high?",
  "Show regional performance",
  "Which category is declining?",
  "Which products should be promoted?",
  "Explain profit margin",
  "Forecast next month",
  "Detect unusual sales",
];

const FOLLOW_UPS = [
  "Would you like to analyze December?",
  "Compare November with October.",
  "Explain category performance.",
  "Analyze regional profitability.",
];

const EXAMPLE_QUESTIONS = [
  "Why was November revenue unusually high?",
  "Which region underperformed?",
  "Why did profit decrease?",
  "Which products should we promote?",
  "Forecast next month's revenue.",
];

const PLACEHOLDER_EXAMPLES = EXAMPLE_QUESTIONS.join("\n");

function ScopedStyles() {
  return (
    <style>{`
      @keyframes aia-fade-in-up {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @keyframes aia-dot-pulse {
        0%, 80%, 100% { opacity: 0.25; transform: scale(0.85); }
        40% { opacity: 1; transform: scale(1); }
      }
      @keyframes aia-glow-pulse {
        0% { box-shadow: 0 0 0 0 rgba(124, 58, 237, 0.35); }
        70% { box-shadow: 0 0 0 12px rgba(124, 58, 237, 0); }
        100% { box-shadow: 0 0 0 0 rgba(124, 58, 237, 0); }
      }
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      .aia-fade-in { animation: aia-fade-in-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) both; }
      .aia-dot { animation: aia-dot-pulse 1.4s infinite ease-in-out; }
      .aia-dot:nth-child(2) { animation-delay: 0.2s; }
      .aia-dot:nth-child(3) { animation-delay: 0.4s; }
      .aia-ask-btn:not(:disabled):hover { transform: translateY(-2px) scale(1.02); box-shadow: 0 14px 30px rgba(124, 58, 237, 0.35); }
      .aia-ask-btn:not(:disabled):active { transform: translateY(0) scale(0.97); }
      .aia-chip:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(124, 58, 237, 0.16); border-color: #7c3aed; }
      .aia-example:hover { color: #7c3aed; text-decoration: underline; }
      .aia-card:hover { transform: translateY(-2px); box-shadow: 0 16px 34px rgba(124, 58, 237, 0.12); border-color: #c4b5fd; }
      .aia-rec-card:hover { transform: translateY(-2px); box-shadow: 0 12px 26px rgba(124, 58, 237, 0.14); border-color: #7c3aed; }
      .aia-history-item:hover { background: #f3f0ff; }
      .aia-followup:hover { background: #ede9fe; border-color: #7c3aed; }
      .aia-retry:hover { background: #b91c1c; }
      @media (max-width: 900px) {
        .aia-layout { grid-template-columns: 1fr !important; }
        .aia-history-panel { order: 2; }
      }
    `}</style>
  );
}

function LoadingDots() {
  return (
    <span style={{ display: "inline-flex", gap: 3 }}>
      <span className="aia-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "white" }} />
      <span className="aia-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "white" }} />
      <span className="aia-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "white" }} />
    </span>
  );
}

function ResponseCard({ icon, title, delay, children }) {
  return (
    <div
      className="aia-fade-in aia-card"
      style={{
        background: "white",
        border: `1px solid ${PANEL_BORDER}`,
        borderRadius: 16,
        padding: 22,
        boxShadow: "0 4px 16px rgba(124, 58, 237, 0.06)",
        transition: "transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease",
        animationDelay: `${delay}s`,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <div
          style={{
            width: 30,
            height: 30,
            borderRadius: 9,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#f3f0ff",
            color: VIOLET,
          }}
        >
          {icon}
        </div>
        <h3 style={{ fontSize: 15.5, fontWeight: 700, color: INK }}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

function AIAnalyst() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuestion, setLastQuestion] = useState("");

  // Session-only conversation history — newest first. React state only,
  // nothing is persisted to local storage.
  const [history, setHistory] = useState([]);
  const [activeId, setActiveId] = useState(null);

  const activeEntry = history.find((h) => h.id === activeId) ?? null;

  const runQuery = async (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    setLastQuestion(trimmed);
    setLoading(true);
    setError(null);

    try {
      const result = await queryAIAnalyst(trimmed);
      const trendResult = await getMonthlyTrend();

      const entry = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        question: trimmed,
        response: result,
        monthlyTrend: trendResult?.data ?? [],
      };

      setHistory((prev) => [entry, ...prev]);
      setActiveId(entry.id);
      setQuestion("");
    } catch (err) {
      console.error(err);
      setError(
        "I ran into a problem analyzing that question. Let's give it another try."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAskClick = () => runQuery(question);

  const handleChipClick = (text) => {
    setQuestion(text);
    runQuery(text);
  };

  const handleFollowUpClick = (text) => runQuery(text);

  const handleHistoryClick = (id) => {
    setActiveId(id);
    setError(null);
  };

  const handleRetry = () => runQuery(lastQuestion);

  const response = activeEntry?.response;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
      <ScopedStyles />

      {/* ---------------- HERO ---------------- */}
      <header
        style={{
          padding: "28px 32px",
          borderRadius: 18,
          background: `linear-gradient(135deg, ${INDIGO} 0%, ${VIOLET} 55%, ${PINK} 100%)`,
          color: "white",
          boxShadow: "0 16px 36px rgba(124, 58, 237, 0.28)",
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
            color: "#e9d5ff",
          }}
        >
          <Sparkles size={14} />
          Flagship Feature
        </span>
        <h1 style={{ fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em", margin: "10px 0 6px" }}>
          🧠 AI Business Analyst
        </h1>
        <p style={{ color: "#ede9fe", fontSize: 14.5, maxWidth: 620 }}>
          Ask questions about your business in natural language and receive
          AI-powered insights.
        </p>
      </header>

      {/* ---------------- SECTION 1: CHAT INPUT ---------------- */}
      <section
        style={{
          background: "white",
          border: `1px solid ${PANEL_BORDER}`,
          borderRadius: 18,
          padding: 22,
          boxShadow: "0 4px 18px rgba(124, 58, 237, 0.06)",
        }}
      >
        <textarea
          rows={4}
          value={question}
          placeholder={PLACEHOLDER_EXAMPLES}
          onChange={(e) => setQuestion(e.target.value)}
          style={{
            width: "100%",
            padding: 16,
            borderRadius: 14,
            border: `1.5px solid ${PANEL_BORDER}`,
            fontSize: 15,
            fontFamily: "inherit",
            resize: "vertical",
            outline: "none",
          }}
        />

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }}>
          <button
            className="aia-ask-btn"
            onClick={handleAskClick}
            disabled={loading}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 10,
              padding: "13px 26px",
              borderRadius: 12,
              border: "none",
              background: loading
                ? "#a78bfa"
                : `linear-gradient(135deg, ${INDIGO}, ${VIOLET})`,
              color: "white",
              fontWeight: 700,
              fontSize: 15,
              cursor: loading ? "progress" : "pointer",
              transition: "transform 0.15s ease, box-shadow 0.2s ease, background 0.2s ease",
            }}
          >
            {loading ? (
              <>
                <LoadingDots />
                Analyzing...
              </>
            ) : (
              <>
                <Send size={17} />
                Analyze
              </>
            )}
          </button>
        </div>

        {/* ---------------- SECTION 2: SUGGESTED QUESTIONS ---------------- */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16 }}>
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              className="aia-chip"
              onClick={() => handleChipClick(q)}
              disabled={loading}
              style={{
                padding: "8px 16px",
                borderRadius: 999,
                border: `1px solid ${PANEL_BORDER}`,
                background: PANEL_BG,
                color: VIOLET,
                fontSize: 13,
                fontWeight: 600,
                cursor: loading ? "default" : "pointer",
                transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      {/* ---------------- MAIN LAYOUT: HISTORY + RESPONSE ---------------- */}
      <div
        className="aia-layout"
        style={{ display: "grid", gridTemplateColumns: "260px minmax(0, 1fr)", gap: 22 }}
      >
        {/* ---------------- SECTION 3: CONVERSATION HISTORY (LEFT) ---------------- */}
        <aside
          className="aia-history-panel"
          style={{
            background: "white",
            border: `1px solid ${PANEL_BORDER}`,
            borderRadius: 16,
            padding: 16,
            display: "flex",
            flexDirection: "column",
            gap: 6,
            height: "fit-content",
            boxShadow: "0 4px 16px rgba(124, 58, 237, 0.05)",
          }}
        >
          <h3
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              fontWeight: 700,
              color: INK,
              padding: "4px 8px 10px",
            }}
          >
            <Clock size={14} color={VIOLET} />
            Conversation History
          </h3>

          {history.length === 0 ? (
            <p style={{ fontSize: 12.5, color: SUBTEXT, padding: "0 8px" }}>
              Your questions will appear here.
            </p>
          ) : (
            history.map((entry) => (
              <button
                key={entry.id}
                className="aia-history-item"
                onClick={() => handleHistoryClick(entry.id)}
                style={{
                  textAlign: "left",
                  padding: "10px 10px",
                  borderRadius: 10,
                  border: "none",
                  background: entry.id === activeId ? "#ede9fe" : "transparent",
                  color: entry.id === activeId ? VIOLET : INK,
                  fontSize: 13,
                  fontWeight: entry.id === activeId ? 700 : 500,
                  cursor: "pointer",
                  transition: "background 0.15s ease",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 8,
                }}
              >
                <MessageSquare size={14} style={{ marginTop: 2, flexShrink: 0 }} />
                <span style={{ lineHeight: 1.4 }}>{entry.question}</span>
              </button>
            ))
          )}
        </aside>

        {/* ---------------- MAIN RESPONSE AREA ---------------- */}
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {/* SECTION 8: EMPTY STATE */}
          {history.length === 0 && !loading && !error && (
            <div
              className="aia-fade-in"
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
                gap: 12,
                padding: "56px 24px",
                borderRadius: 18,
                border: `1.5px dashed ${PANEL_BORDER}`,
                background: PANEL_BG,
              }}
            >
              <div
                style={{
                  width: 68,
                  height: 68,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: `linear-gradient(135deg, ${INDIGO}, ${VIOLET})`,
                  animation: "aia-glow-pulse 2.4s infinite",
                }}
              >
                <Brain size={32} color="white" />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: INK }}>
                Start asking questions about your business.
              </h3>
              <p style={{ fontSize: 13.5, color: SUBTEXT, maxWidth: 380 }}>
                Try one of the suggested questions above, or one of these:
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    className="aia-example"
                    onClick={() => handleChipClick(q)}
                    style={{
                      background: "none",
                      border: "none",
                      padding: 0,
                      fontSize: 13.5,
                      color: VIOLET,
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <ArrowRight size={13} />
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* LOADING STATE */}
          {loading && (
            <div
              className="aia-fade-in"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                padding: "26px 24px",
                borderRadius: 16,
                background: `linear-gradient(135deg, ${INDIGO}, ${VIOLET})`,
                color: "white",
              }}
            >
              <Loader2 size={22} style={{ animation: "spin 1s linear infinite" }} />
              <div>
                <p style={{ fontWeight: 700, fontSize: 15 }}>
                  AI is analyzing your business...
                </p>
                <p style={{ fontSize: 13, color: "#e9d5ff" }}>
                  This usually takes a few seconds.
                </p>
              </div>
            </div>
          )}

          {/* SECTION 9: ERROR STATE */}
          {error && !loading && (
            <div
              className="aia-fade-in"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 16,
                padding: "20px 24px",
                borderRadius: 16,
                background: "#fef2f2",
                border: "1px solid #fecaca",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <AlertCircle size={22} color="#dc2626" />
                <div>
                  <p style={{ fontWeight: 700, fontSize: 14.5, color: "#991b1b" }}>
                    {error}
                  </p>
                  <p style={{ fontSize: 12.5, color: "#b91c1c" }}>
                    Your question wasn't lost — just hit retry.
                  </p>
                </div>
              </div>

              <button
                className="aia-retry"
                onClick={handleRetry}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "9px 18px",
                  borderRadius: 10,
                  border: "none",
                  background: "#dc2626",
                  color: "white",
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: "pointer",
                  transition: "background 0.2s ease",
                }}
              >
                <RefreshCw size={14} />
                Retry
              </button>
            </div>
          )}

          {/* SECTION 4: AI RESPONSE */}
          {response && !loading && (
            <>
              <ResponseCard icon={<Sparkles size={16} />} title="Executive Summary" delay={0}>
                <p style={{ fontSize: 14, color: "#3f3a52", lineHeight: 1.6, margin: 0 }}>
                  {response.executive_summary}
                </p>
              </ResponseCard>

              <ResponseCard icon={<Lightbulb size={16} />} title="Key Findings" delay={0.05}>
                <ul style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 6 }}>
                  {response.key_findings?.map((item, i) => (
                    <li key={i} style={{ fontSize: 14, color: "#3f3a52", lineHeight: 1.5 }}>
                      {item}
                    </li>
                  ))}
                </ul>
              </ResponseCard>

              <ResponseCard icon={<Gauge size={16} />} title="Confidence" delay={0.1}>
                <span
                  style={{
                    display: "inline-block",
                    padding: "4px 14px",
                    borderRadius: 999,
                    background: "#ede9fe",
                    color: VIOLET,
                    fontWeight: 700,
                    fontSize: 13,
                    marginBottom: 8,
                  }}
                >
                  {response.confidence}
                </span>
                <p style={{ fontSize: 13.5, color: SUBTEXT, margin: 0 }}>
                  {response.confidence_reason}
                </p>
              </ResponseCard>

              <ResponseCard icon={<Target size={16} />} title="Priority Actions" delay={0.15}>
                <ul style={{ margin: 0, paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
                  {response.priority_actions?.map((action, i) => (
                    <li
                      key={i}
                      style={{
                        padding: "10px 12px",
                        borderRadius: 10,
                        background: PANEL_BG,
                        border: `1px solid ${PANEL_BORDER}`,
                        fontSize: 13.5,
                        color: "#3f3a52",
                      }}
                    >
                      <strong style={{ color: VIOLET }}>{action.priority}</strong> — {action.action}
                      <br />
                      <small style={{ color: SUBTEXT }}>{action.reason}</small>
                    </li>
                  ))}
                </ul>
              </ResponseCard>

              <ResponseCard icon={<FlaskConical size={16} />} title="Recommended Experiments" delay={0.2}>
                <ul style={{ margin: 0, paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
                  {response.experiments?.map((exp, i) => (
                    <li
                      key={i}
                      style={{
                        padding: "10px 12px",
                        borderRadius: 10,
                        background: PANEL_BG,
                        border: `1px solid ${PANEL_BORDER}`,
                        fontSize: 13.5,
                        color: "#3f3a52",
                      }}
                    >
                      <strong>{exp.experiment}</strong>
                      <br />
                      <small style={{ color: SUBTEXT }}>
                        Success Metric: {exp.success_metric}
                      </small>
                    </li>
                  ))}
                </ul>
              </ResponseCard>

              <ResponseCard icon={<CheckCircle2 size={16} />} title="Monitoring Metrics" delay={0.25}>
                <ul style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 6 }}>
                  {response.monitoring_metrics?.map((metric, i) => (
                    <li key={i} style={{ fontSize: 14, color: "#3f3a52" }}>
                      {metric}
                    </li>
                  ))}
                </ul>
              </ResponseCard>

              <ResponseCard icon={<Wrench size={16} />} title="Tools Used" delay={0.3}>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {response.tools_used?.map((tool, i) => (
                    <span
                      key={i}
                      style={{
                        padding: "5px 12px",
                        borderRadius: 999,
                        background: "#ede9fe",
                        color: VIOLET,
                        fontSize: 12.5,
                        fontWeight: 700,
                      }}
                    >
                      {tool.tool}
                    </span>
                  ))}
                </div>
              </ResponseCard>

              {/* SECTION 5: EVIDENCE CHART */}
              {activeEntry.monthlyTrend.length > 0 && (
                <div
                  className="aia-fade-in aia-card"
                  style={{
                    background: "white",
                    border: `1px solid ${PANEL_BORDER}`,
                    borderRadius: 16,
                    padding: 22,
                    boxShadow: "0 4px 16px rgba(124, 58, 237, 0.06)",
                    transition: "transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease",
                    animationDelay: "0.35s",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <div
                      style={{
                        width: 30,
                        height: 30,
                        borderRadius: 9,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "#f3f0ff",
                        color: VIOLET,
                      }}
                    >
                      <BarChart3 size={16} />
                    </div>
                    <h3 style={{ fontSize: 15.5, fontWeight: 700, color: INK }}>
                      Evidence Supporting the Analysis
                    </h3>
                  </div>

                  <p style={{ fontSize: 12.5, color: SUBTEXT, margin: "0 0 14px 38px" }}>
                    Supporting context for the analysis above — not the main
                    finding.
                  </p>

                  <div style={{ width: "100%", height: 220 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={activeEntry.monthlyTrend}>
                        <defs>
                          <linearGradient id="aiaRevenueGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={VIOLET} stopOpacity={0.35} />
                            <stop offset="100%" stopColor={VIOLET} stopOpacity={0} />
                          </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="Order_Date" tick={{ fontSize: 11 }} />
                        <YAxis
                          tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`}
                          tick={{ fontSize: 11 }}
                        />
                        <Tooltip />

                        <Area
                          type="monotone"
                          dataKey="Revenue"
                          stroke={VIOLET}
                          strokeWidth={2.5}
                          fill="url(#aiaRevenueGradient)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* SECTION 6: BUSINESS RECOMMENDATIONS */}
              {response.priority_actions?.length > 0 && (
                <div>
                  <h3
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 15,
                      fontWeight: 700,
                      color: INK,
                      marginBottom: 10,
                    }}
                  >
                    <Lightbulb size={16} color={VIOLET} />
                    Business Recommendations
                  </h3>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                      gap: 12,
                    }}
                  >
                    {response.priority_actions.map((action, i) => (
                      <div
                        key={i}
                        className="aia-fade-in aia-rec-card"
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 10,
                          padding: "14px 16px",
                          borderRadius: 12,
                          background: "white",
                          border: `1px solid ${PANEL_BORDER}`,
                          transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
                          animationDelay: `${0.05 * i}s`,
                        }}
                      >
                        <ArrowRight size={16} color={VIOLET} style={{ marginTop: 2, flexShrink: 0 }} />
                        <span style={{ fontSize: 13.5, color: "#3f3a52", lineHeight: 1.5 }}>
                          {action.action}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SECTION 7: FOLLOW-UP QUESTIONS */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {FOLLOW_UPS.map((text) => (
                  <button
                    key={text}
                    className="aia-followup"
                    onClick={() => handleFollowUpClick(text)}
                    disabled={loading}
                    style={{
                      padding: "9px 16px",
                      borderRadius: 999,
                      border: `1px solid ${PANEL_BORDER}`,
                      background: "white",
                      color: VIOLET,
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: loading ? "default" : "pointer",
                      transition: "background 0.2s ease, border-color 0.2s ease",
                    }}
                  >
                    {text}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default AIAnalyst;