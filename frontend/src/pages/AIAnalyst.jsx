// src/pages/AIAnalyst.jsx
import React, { useState, useRef, useEffect } from "react";
import {
  Brain,
  Sparkles,
  Trash2,
  User
} from "lucide-react";

import { queryAIAnalyst } from "../services/api";

// Import all required modular AI chat components
import AIResponseCard from "../components/AIResponseCard";
import TypingIndicator from "../components/TypingIndicator";
import ChatInput from "../components/ChatInput";
import SuggestedQuestions from "../components/SuggestedQuestions";

const INDIGO = "#1e1b4b";
const BLUE_DARK = "#0f172a";
const BLUE_LIGHT = "#312e81";
const ACCENT = "#6366f1";
const ACCENT_LIGHT = "#a5b4fc";
const BG_LIGHT = "#f8fafc";
const BORDER = "#e2e8f0";

const SUGGESTED_QUESTIONS = [
  "Why did revenue increase last month?",
  "Compare East vs West performance.",
  "Forecast revenue for the next quarter.",
  "Show me recent anomalies.",
  "What are our worst performing products?",
];

function ScopedStyles() {
  return (
    <style>{`
      /* Root layout & responsiveness */
      .aia-page { display: flex; flex-direction: column; gap: 20px; height: calc(100vh - 40px); max-width: 1300px; margin: 0 auto; width: 100%; box-sizing: border-box; }
      
      .aia-hero {
        background: linear-gradient(135deg, ${BLUE_DARK} 0%, ${INDIGO} 55%, ${BLUE_LIGHT} 100%);
        border-radius: 16px; padding: 24px 32px; color: white;
        box-shadow: 0 14px 34px rgba(15, 23, 42, 0.22); flex-shrink: 0;
      }
      .aia-eyebrow { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: ${ACCENT_LIGHT}; }
      
      .aia-chat-container {
        display: flex; flex-direction: column; flex-grow: 1; overflow: hidden;
        background: white; border: 1px solid ${BORDER}; border-radius: 16px;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05); position: relative;
      }
      
      .aia-messages-area {
        flex-grow: 1; overflow-y: auto; padding: 32px; display: flex; flex-direction: column; gap: 28px;
        scroll-behavior: smooth;
      }
      
      .aia-input-area {
        padding: 20px 32px; border-top: 1px solid ${BORDER}; background: ${BG_LIGHT};
        border-radius: 0 0 16px 16px;
      }
      
      /* Message Layout: Comfortable reading width (~75-80% for AI, compact for User) */
      .aia-msg-row { display: flex; gap: 16px; width: 100%; animation: aiaFadeSlideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; }
      .aia-msg-row.user { justify-content: flex-end; }
      .aia-msg-row.ai { justify-content: flex-start; }
      
      .aia-msg-inner {
        display: flex; gap: 16px; width: 100%; max-width: 80%;
      }
      .aia-msg-row.user .aia-msg-inner {
        flex-direction: row-reverse; max-width: 70%;
      }

      @media (max-width: 768px) {
        .aia-msg-inner { max-width: 100% !important; }
        .aia-messages-area { padding: 16px; }
        .aia-hero { padding: 16px 20px; }
        .aia-input-area { padding: 14px 16px; }
      }

      .aia-avatar { width: 38px; height: 38px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
      .aia-avatar.ai { background: linear-gradient(135deg, ${ACCENT}, #4f46e5); color: white; }
      .aia-avatar.user { background: #334155; color: white; }
      
      .aia-bubble { padding: 22px 26px; border-radius: 16px; font-size: 15px; line-height: 1.65; width: 100%; }
      .aia-bubble.ai { background: white; border: 1px solid ${BORDER}; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04); border-top-left-radius: 4px; color: #1e293b; }
      .aia-bubble.user { background: linear-gradient(135deg, ${BLUE_LIGHT}, ${ACCENT}); color: white; border-top-right-radius: 4px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.22); font-weight: 500; }
      
      /* Actions */
      .aia-action-bar { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 32px 0; }
      .aia-action-btn { display: inline-flex; align-items: center; gap: 6px; background: transparent; border: none; color: #64748b; font-size: 12.5px; font-weight: 600; cursor: pointer; transition: color 0.2s; padding: 6px 12px; border-radius: 6px; }
      .aia-action-btn:hover { background: ${BG_LIGHT}; color: ${ACCENT}; }

      /* Enhanced Markdown Typography */
      .markdown-body { font-size: 15px; color: #334155; line-height: 1.7; }
      .markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 { color: ${BLUE_DARK}; font-weight: 700; margin-top: 20px; margin-bottom: 10px; }
      .markdown-body h1 { font-size: 22px; border-bottom: 1px solid ${BORDER}; padding-bottom: 6px; }
      .markdown-body h2 { font-size: 19px; }
      .markdown-body h3 { font-size: 16.5px; color: ${BLUE_LIGHT}; font-weight: 700; }
      .markdown-body p { margin-bottom: 14px; }
      .markdown-body strong { font-weight: 700; color: ${BLUE_DARK}; }
      .markdown-body em { font-style: italic; }
      .markdown-body ul, .markdown-body ol { margin-bottom: 14px; padding-left: 22px; }
      .markdown-body li { margin-bottom: 6px; }
      .markdown-body blockquote { border-left: 3.5px solid ${ACCENT}; padding-left: 14px; color: #475569; margin: 14px 0; font-style: italic; background: ${BG_LIGHT}; padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0; }
      .markdown-body code { background: ${BG_LIGHT}; border: 1px solid ${BORDER}; padding: 3px 7px; border-radius: 6px; font-size: 13.5px; font-family: monospace; color: ${INDIGO}; }
      .markdown-body pre { background: ${BLUE_DARK}; color: white; padding: 16px; border-radius: 10px; overflow-x: auto; margin: 16px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
      .markdown-body pre code { background: transparent; border: none; color: white; padding: 0; }
      .markdown-body table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; border-radius: 8px; overflow: hidden; border: 1px solid ${BORDER}; }
      .markdown-body th, .markdown-body td { border: 1px solid ${BORDER}; padding: 10px 14px; text-align: left; }
      .markdown-body th { background: ${BG_LIGHT}; font-weight: 700; color: ${BLUE_DARK}; }
      .markdown-body a { color: ${ACCENT}; text-decoration: underline; text-underline-offset: 3px; }
      
      /* Smooth Animation Keyframes */
      @keyframes aiaFadeSlideIn { 
        0% { opacity: 0; transform: translateY(12px); } 
        100% { opacity: 1; transform: translateY(0); } 
      }
    `}</style>
  );
}

/**
 * AIAnalyst - Clean orchestration component managing state, conversation history,
 * API requests, loading states, and delegating presentation to reusable components.
 */
function AIAnalyst() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("");
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, loadingStatus]);

  // Loading status messages reflecting the real agentic pipeline stages
  useEffect(() => {
    let timer;
    if (isTyping) {
      const statuses = [
        "Planning analysis strategy...",
        "Extracting business entities...",
        "Executing analytical tools...",
        "Analysing evidence...",
        "Generating business insights...",
        "Running validation & reflection..."
      ];
      let idx = 0;
      setLoadingStatus(statuses[0]);
      timer = setInterval(() => {
        idx = (idx + 1) % statuses.length;
        setLoadingStatus(statuses[idx]);
      }, 1800);
    } else {
      setLoadingStatus("");
    }
    return () => clearInterval(timer);
  }, [isTyping]);

  /**
   * Handle sending a message to the AI Analyst backend API.
   */
  const handleSend = async (textOverride) => {
    const text = textOverride || inputValue;
    if (!text.trim()) return;

    const userMsg = { id: Date.now().toString(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);

    try {
      const result = await queryAIAnalyst(text);
      console.log("FULL API RESULT:", JSON.stringify(result, null, 2));
      console.log("EVIDENCE:", JSON.stringify(result.evidence, null, 2));

      const evidenceObject = result.evidence || {};
      
      const aiMsg = {
          id: (Date.now() + 1).toString(),
          role: "ai",

          // AI response
          content: result.final_response,

          // NEW
          visualization: result.visualization,

          // NEW
          evidence: result.evidence,

          toolsUsed: result.metadata?.tools_used || [],

          executionTime:
              result.metadata?.execution_time_seconds ?? 0,

          confidence:
              result.metadata?.confidence ?? 0,

          evidenceCount:
              result.metadata?.evidence_count ?? 0,

          followUpQuestions:
              result.final_response?.suggested_follow_up_questions || []
      };
      
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error("AI Analyst error:", error?.response?.data || error.message);

      // Determine a user-friendly error message
      const serverMsg = error?.response?.data?.detail?.message
        || error?.response?.data?.message
        || null;
      const statusCode = error?.response?.status;
      let displayMsg = serverMsg
        || (statusCode === 500
          ? "The analysis pipeline encountered an internal error. Please try a different question or retry."
          : statusCode === 422
          ? "Your question could not be processed. Please rephrase and try again."
          : "Unable to reach the InsightsOps server. Please check the backend is running.");

      const errorMsg = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        content: {
          executive_summary: `⚠️ Analysis Error: ${displayMsg}`,
          key_findings: [],
          evidence: [],
          business_insights: [],
          recommendations: [],
          potential_risks: [],
          suggested_follow_up_questions: [
            "Try rephrasing your question.",
            "Ask about overall revenue performance.",
            "Which region generated the highest revenue?"
          ]
        },
        visualization: null,
        evidence: {},
        toolsUsed: [],
        executionTime: 0,
        confidence: 0,
        evidenceCount: 0,
        followUpQuestions: []
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const clearChat = () => setMessages([]);

  return (
    <div className="aia-page">
      <ScopedStyles />

      {/* HEADER HERO */}
      <header className="aia-hero">
        <span className="aia-eyebrow">
          <Sparkles size={14} /> Intelligence Platform Workspace
        </span>
        <h1 style={{ fontSize: 26, fontWeight: 700, margin: "6px 0 4px" }}>
          AI Business Analyst
        </h1>
        <p style={{ color: ACCENT_LIGHT, fontSize: 14, margin: 0, fontWeight: 400 }}>
          Interact with your enterprise datasets using natural language queries and live automated analytics.
        </p>
      </header>

      {/* CHAT CONTAINER */}
      <div className="aia-chat-container">
        
        {/* CLEAR CHAT ACTION */}
        <div className="aia-action-bar">
          <button className="aia-action-btn" onClick={clearChat} disabled={messages.length === 0}>
            <Trash2 size={14} /> Clear Conversation
          </button>
        </div>

        {/* MESSAGES & EMPTY STATE AREA */}
        <div className="aia-messages-area">
          {messages.length === 0 ? (
            /* Delegated to SuggestedQuestions component */
            <SuggestedQuestions 
              suggestions={SUGGESTED_QUESTIONS} 
              onSelect={(question) => handleSend(question)} 
            />
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`aia-msg-row ${msg.role}`}>
                <div className="aia-msg-inner">
                  <div className={`aia-avatar ${msg.role}`}>
                    {msg.role === "ai" ? <Brain size={20} /> : <User size={20} />}
                  </div>
                  
                  {msg.role === "user" ? (
                    <div className="aia-bubble user">
                      {msg.content}
                    </div>
                  ) : (
                    /* Delegated to AIResponseCard component (which internally uses AIChartRenderer & MetadataPanel) */
                    <AIResponseCard 
                      message={msg} 
                      onSelectFollowUp={(question) => handleSend(question)} 
                    />
                  )}
                </div>
              </div>
            ))
          )}

          {/* Delegated to TypingIndicator component */}
          <TypingIndicator isTyping={isTyping} loadingStatus={loadingStatus} />

          {/* Auto-scroll anchor */}
          <div ref={messagesEndRef} />
        </div>

        {/* INPUT AREA */}
        <div className="aia-input-area">
          {/* Delegated to ChatInput component */}
          <ChatInput
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onSend={() => handleSend()}
            isLoading={isTyping}
            placeholder="Ask a business question or request analytics (e.g., Show revenue in West region)..."
          />
        </div>

      </div>
    </div>
  );
}

export default AIAnalyst;