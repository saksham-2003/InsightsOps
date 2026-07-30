// src/components/ChatInput.jsx
import React, { useRef, useEffect } from "react";
import { Send } from "lucide-react";

const ACCENT = "#6366f1";
const BORDER = "#cbd5e1";
const BG_LIGHT = "#f8fafc";

/**
 * ChatInput - A production-ready, reusable AI chat input component
 * featuring auto-resizing textarea, Enter to send (Shift+Enter for newline),
 * character counter, mobile responsiveness, and accessibility support.
 */
export default function ChatInput({
  value,
  onChange,
  onSend,
  isLoading,
  placeholder = "Ask a business question or request analytics...",
  maxLength = 1000,
}) {
  const textareaRef = useRef(null);

  // Requirement 2: Auto-resize textarea as the user types
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
    }
  }, [value]);

  // Requirement 3 & 4: Handle keyboard actions (Enter to send, Shift+Enter for newline)
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) {
        onSend();
      }
    }
  };

  const handleChange = (e) => {
    if (e.target.value.length <= maxLength) {
      onChange(e);
    }
  };

  const isSendDisabled = !value.trim() || isLoading;

  return (
    <div className="chat-input-wrapper">
      <style>{`
        .chat-input-wrapper {
          display: flex;
          flex-direction: column;
          background: white;
          border: 1px solid ${BORDER};
          border-radius: 16px;
          padding: 12px 16px;
          box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
          transition: border-color 0.2s, box-shadow 0.2s;
          width: 100%;
          box-sizing: border-box;
        }
        .chat-input-wrapper:focus-within {
          border-color: ${ACCENT};
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12), 0 4px 20px rgba(15, 23, 42, 0.06);
        }
        .chat-textarea {
          flex-grow: 1;
          border: none;
          outline: none;
          font-family: inherit;
          font-size: 15px;
          line-height: 1.5;
          resize: none;
          background: transparent;
          color: #0f172a;
          max-height: 180px;
          box-sizing: border-box;
        }
        .chat-textarea::placeholder {
          color: #94a3b8;
        }
        .chat-input-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid #f1f5f9;
        }
        .chat-char-counter {
          font-size: 11.5px;
          color: #94a3b8;
          font-weight: 500;
        }
        .chat-send-btn {
          background: ${ACCENT};
          color: white;
          border: none;
          padding: 10px 14px;
          border-radius: 10px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .chat-send-btn:not(:disabled):hover {
          background: #4f46e5;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
        }
        .chat-send-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
          background: #cbd5e1;
        }
        @media (max-width: 768px) {
          .chat-input-wrapper {
            padding: 10px 12px;
          }
          .chat-textarea {
            font-size: 14px;
          }
        }
      `}</style>

      {/* Requirement 1: Multi-line textarea with auto-resize */}
      <textarea
        ref={textareaRef}
        className="chat-textarea"
        rows={1}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        // Requirement 5: Disable input while isLoading is true
        disabled={isLoading}
        placeholder={placeholder}
        maxLength={maxLength}
        aria-label="Chat input message box"
      />

      <div className="chat-input-footer">
        {/* Requirement 7: Character counter */}
        <span className="chat-char-counter" aria-live="polite">
          {value.length}/{maxLength}
        </span>

        {/* Requirement 10: Show a Send icon instead of plain text */}
        <button
          className="chat-send-btn"
          onClick={onSend}
          // Requirement 5 & 6: Disable Send button if empty or loading
          disabled={isSendDisabled}
          aria-label="Send message"
          type="button"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}