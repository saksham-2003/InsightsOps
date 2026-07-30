// src/components/SuggestedQuestions.jsx
import React from "react";
import {
  TrendingUp,
  BarChart3,
  DollarSign,
  AlertTriangle,
  Package,
  Users,
  Compass,
  PieChart,
  Activity
} from "lucide-react";

const ACCENT = "#6366f1";
const BORDER = "#e2e8f0";
const BG_LIGHT = "#f8fafc";
const BLUE_DARK = "#0f172a";

// Default suggestions specified in requirements 4
const DEFAULT_SUGGESTIONS = [
  "Which region generated the highest revenue?",
  "Show monthly sales trends.",
  "Which products generated the highest profit?",
  "Detect unusual sales anomalies.",
  "Forecast revenue for the next 6 months.",
  "Compare category performance.",
  "Which customers generated the most revenue?",
  "Why did profit decrease in the South region?",
];

/**
 * Helper function to select an appropriate icon based on keywords in the question text.
 */
const getSuggestionIcon = (question) => {
  const q = question.toLowerCase();
  if (q.includes("revenue") || q.includes("sales") || q.includes("profit") || q.includes("highest profit")) {
    return <DollarSign size={18} color={ACCENT} />;
  }
  if (q.includes("forecast") || q.includes("months") || q.includes("trend")) {
    return <TrendingUp size={18} color={ACCENT} />;
  }
  if (q.includes("anomaly") || q.includes("unusual") || q.includes("decrease")) {
    return <AlertTriangle size={18} color={ACCENT} />;
  }
  if (q.includes("product") || q.includes("item")) {
    return <Package size={18} color={ACCENT} />;
  }
  if (q.includes("customer") || q.includes("client")) {
    return <Users size={18} color={ACCENT} />;
  }
  if (q.includes("region") || q.includes("south")) {
    return <Compass size={18} color={ACCENT} />;
  }
  if (q.includes("category") || q.includes("compare")) {
    return <PieChart size={18} color={ACCENT} />;
  }
  return <BarChart3 size={18} color={ACCENT} />;
};

/**
 * SuggestedQuestions - A modern, responsive "Suggested Questions" component
 * styled like ChatGPT, Microsoft Copilot, or Perplexity prompt cards.
 */
export default function SuggestedQuestions({ suggestions = DEFAULT_SUGGESTIONS, onSelect }) {
  const listToDisplay = suggestions && suggestions.length > 0 ? suggestions : DEFAULT_SUGGESTIONS;

  return (
    <div className="suggested-questions-container">
      <style>{`
        .suggested-questions-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 100%;
          max-width: 900px;
          margin: 0 auto;
          padding: 20px 16px;
          box-sizing: border-box;
        }
        .suggested-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 14px;
          width: 100%;
          margin-top: 16px;
        }
        /* Tablet: 2 columns */
        @media (max-width: 1024px) {
          .suggested-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
        /* Mobile: 1 column */
        @media (max-width: 640px) {
          .suggested-grid {
            grid-template-columns: 1fr;
          }
        }
        .suggested-card {
          background: white;
          border: 1px solid ${BORDER};
          border-radius: 14px;
          padding: 16px 20px;
          display: flex;
          align-items: flex-start;
          gap: 14px;
          cursor: pointer;
          transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
          box-shadow: 0 2px 6px rgba(15, 23, 42, 0.02);
          text-align: left;
          box-sizing: border-box;
        }
        .suggested-card:hover {
          border-color: ${ACCENT};
          transform: translateY(-3px);
          box-shadow: 0 8px 24px rgba(99, 102, 241, 0.12);
          background: #fdfdff;
        }
        .suggested-icon-wrap {
          padding: 10px;
          background: ${BG_LIGHT};
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: background 0.2s;
        }
        .suggested-card:hover .suggested-icon-wrap {
          background: #e0e7ff;
        }
        .suggested-text {
          font-size: 14px;
          font-weight: 600;
          color: #334155;
          line-height: 1.4;
          margin: 0;
        }
      `}</style>

      {/* Responsive Grid of Suggestion Cards */}
      <div className="suggested-grid">
        {listToDisplay.map((question, idx) => (
          <button
            key={idx}
            className="suggested-card"
            onClick={() => onSelect && onSelect(question)}
            type="button"
            aria-label={`Suggested question: ${question}`}
          >
            <div className="suggested-icon-wrap">
              {getSuggestionIcon(question)}
            </div>
            <p className="suggested-text">
              {question}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}