// src/components/FollowUpChips.jsx
import React from "react";
import { ArrowRight, Sparkles } from "lucide-react";

const ACCENT = "#6366f1";
const BORDER = "#e2e8f0";

/**
 * FollowUpChips - A reusable, modern follow-up questions component
 * styled like ChatGPT, Claude, Microsoft Copilot, and Perplexity.
 * Displays AI-generated follow-up questions as interactive chips with icons and hover animations.
 */
export default function FollowUpChips({ followUpQuestions = [], onSelect }) {
  // Requirement 3: If followUpQuestions is empty, display nothing.
  if (!Array.isArray(followUpQuestions) || followUpQuestions.length === 0) {
    return null;
  }

  return (
    <div className="followup-chips-container" role="region" aria-label="Suggested follow-up questions">
      <style>{`
        .followup-chips-container {
          margin-top: 18px;
          padding-top: 14px;
          border-top: 1px solid ${BORDER};
          box-sizing: border-box;
          width: 100%;
        }
        .followup-header {
          font-size: 11.5px;
          font-weight: 700;
          color: #64748b;
          text-transform: uppercase;
          margin-bottom: 10px;
          display: flex;
          align-items: center;
          gap: 6px;
          letter-spacing: 0.05em;
        }
        .followup-chips-wrapper {
          display: flex;
          flex-wrap: wrap; /* Requirement 5: Support wrapping into multiple rows */
          gap: 8px;
        }
        .followup-chip {
          padding: 8px 14px;
          border-radius: 9999px; /* Modern rounded chips */
          border: 1px solid ${ACCENT}35;
          background: ${ACCENT}08;
          color: ${ACCENT};
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
          display: inline-flex;
          align-items: center;
          gap: 6px;
          box-shadow: 0 1px 3px rgba(99, 102, 241, 0.04); /* Requirement 2: Subtle shadows */
          box-sizing: border-box;
          text-align: left;
        }
        .followup-chip:hover {
          background: ${ACCENT};
          color: white;
          transform: translateY(-2px); /* Requirement 2: Hover animations & smooth transitions */
          box-shadow: 0 6px 16px rgba(99, 102, 241, 0.25);
          border-color: ${ACCENT};
        }
        .followup-chip:focus {
          outline: none;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
        }
      `}</style>

      <div className="followup-header">
        <Sparkles size={13} color={ACCENT} /> Suggested Follow-up Questions
      </div>

      <div className="followup-chips-wrapper">
        {followUpQuestions.map((question, idx) => (
          <button
            key={idx}
            className="followup-chip"
            onClick={() => onSelect && onSelect(question)}
            type="button"
            aria-label={`Ask follow-up: ${question}`}
          >
            {/* Requirement 6: Add an icon before every chip */}
            <ArrowRight size={13} style={{ flexShrink: 0 }} />
            <span>{question}</span>
          </button>
        ))}
      </div>
    </div>
  );
}