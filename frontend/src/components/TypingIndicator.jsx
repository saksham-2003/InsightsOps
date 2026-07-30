// src/components/TypingIndicator.jsx
import React from "react";
import { Brain, Loader2 } from "lucide-react";

const BLUE_DARK = "#0f172a";
const INDIGO = "#1e1b4b";
const ACCENT = "#6366f1";
const ACCENT_LIGHT = "#a5b4fc";
const BORDER = "#e2e8f0";

/**
 * TypingIndicator - A premium, self-contained AI typing indicator component
 * featuring a smooth slide/fade animation, pulsing states, active status messages,
 * and an animated AI avatar.
 */
export default function TypingIndicator({ isTyping, loadingStatus }) {
  if (!isTyping) return null;

  return (
    <>
      <style>{`
        @keyframes aiaFadeSlideIn { 
          0% { opacity: 0; transform: translateY(12px); } 
          100% { opacity: 1; transform: translateY(0); } 
        }
        
        @keyframes aiaPulseGlow { 
          0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 4px 16px rgba(99, 102, 241, 0.15); } 
          50% { opacity: 0.75; transform: scale(0.99); box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08); } 
        }

        @keyframes aiaDotBounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1.0); }
        }

        .aia-typing-row {
          display: flex;
          gap: 16px;
          width: 100%;
          animation: aiaFadeSlideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        .aia-typing-bubble {
          background: white;
          border: 1px solid ${BORDER};
          border-radius: 16px;
          border-top-left-radius: 4px;
          padding: 18px 24px;
          box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
          display: flex;
          align-items: center;
          gap: 14px;
          animation: aiaPulseGlow 2s ease-in-out infinite;
          max-width: 380px;
          width: 100%;
        }

        .aia-typing-dots {
          display: flex;
          align-items: center;
          gap: 4px;
          margin-left: auto;
        }

        .aia-typing-dot {
          width: 6px;
          height: 6px;
          background-color: ${ACCENT};
          border-radius: 50%;
          animation: aiaDotBounce 1.4s infinite ease-in-out both;
        }

        .aia-typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .aia-typing-dot:nth-child(2) { animation-delay: -0.16s; }
        .aia-typing-dot:nth-child(3) { animation-delay: 0s; }
      `}</style>

      <div className="aia-typing-row">
        <div style={{ display: 'flex', gap: 16, width: '100%' }}>
          {/* Requirement 1: Modern AI avatar/icon */}
          <div 
            className="aia-avatar ai"
            style={{
              width: 38,
              height: 38,
              borderRadius: 12,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              background: `linear-gradient(135deg, ${ACCENT}, #4f46e5)`,
              color: 'white',
              boxShadow: '0 2px 6px rgba(0,0,0,0.06)'
            }}
          >
            <Brain size={20} />
          </div>

          {/* Typing Card / Bubble */}
          <div className="aia-typing-bubble">
            <Loader2 
              size={18} 
              color={ACCENT} 
              style={{ animation: "spin 1s linear infinite", flexShrink: 0 }} 
            />
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flexGrow: 1 }}>
              {/* Requirement 3: Display loadingStatus message */}
              <span style={{ fontSize: 14, fontWeight: 700, color: BLUE_DARK, letterSpacing: '-0.01em' }}>
                {loadingStatus || "AI Analyst is thinking..."}
              </span>
              <span style={{ fontSize: 11.5, color: '#64748b', fontWeight: 500 }}>
                InsightsOps Autonomous Engine
              </span>
            </div>

            {/* Requirement 2: Animated loading dots */}
            <div className="aia-typing-dots">
              <div className="aia-typing-dot" />
              <div className="aia-typing-dot" />
              <div className="aia-typing-dot" />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}