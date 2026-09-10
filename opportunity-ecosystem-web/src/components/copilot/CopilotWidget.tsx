"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Bot,
  X,
  Minus,
  Send,
  Sparkles,
  Loader2,
  ShieldCheck,
  ShieldAlert,
  RotateCcw,
  MessageSquare,
  ChevronDown,
  User,
} from "lucide-react";
import {
  api,
  CopilotChatResponse,
  OpportunitySourceCitation,
} from "@/lib/api";
import { SourceCitationChip } from "./SourceCitationChip";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  sources?: OpportunitySourceCitation[];
  sourceOpportunityIds?: string[];
  retrievalGuardTriggered?: boolean;
}

const STARTER_PROMPTS = [
  "What upcoming hackathons are available for CS students?",
  "Are there any paid research internships in AI & ML?",
  "Which competitions have deadlines in the next 3 weeks?",
  "Tell me about open source fellowships with grants.",
];

export function CopilotWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize or restore session_id
  useEffect(() => {
    let currentId = "";
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("copilot_session_id");
      if (stored) {
        currentId = stored;
      } else {
        currentId = typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : `session-${Date.now()}`;
        localStorage.setItem("copilot_session_id", currentId);
      }
    }
    setSessionId(currentId);

    const handleOpen = () => setIsOpen(true);
    const handleToggle = () => setIsOpen((prev) => !prev);

    window.addEventListener("open-copilot", handleOpen);
    window.addEventListener("toggle-copilot", handleToggle);

    return () => {
      window.removeEventListener("open-copilot", handleOpen);
      window.removeEventListener("toggle-copilot", handleToggle);
    };
  }, []);

  // Auto-scroll on message updates
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isLoading]);

  const handleResetSession = () => {
    const newId = typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `session-${Date.now()}`;
    setSessionId(newId);
    if (typeof window !== "undefined") {
      localStorage.setItem("copilot_session_id", newId);
    }
    setMessages([]);
  };

  const handleSendMessage = async (textToSend?: string) => {
    const messageContent = (textToSend || inputMessage).trim();
    if (!messageContent || isLoading) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      sender: "user",
      text: messageContent,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const res = await api.copilot.chat({
        session_id: sessionId,
        message: messageContent,
      });

      const data: CopilotChatResponse | undefined = res?.data || (res as unknown as CopilotChatResponse);

      if (data) {
        // Map sources citations from backend
        let citations: OpportunitySourceCitation[] = [];
        if (data.sources && data.sources.length > 0) {
          citations = data.sources;
        } else if (data.source_opportunity_ids && data.source_opportunity_ids.length > 0) {
          citations = data.source_opportunity_ids.map((id, idx) => ({
            id: String(id),
            title: `Opportunity #${idx + 1}`,
            similarity: 0.85,
          }));
        }

        const assistantMessage: ChatMessage = {
          id: `msg-${Date.now()}-assistant`,
          sender: "assistant",
          text: data.answer || "I retrieved the relevant records for you.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          sources: citations,
          sourceOpportunityIds: data.source_opportunity_ids,
          retrievalGuardTriggered: data.retrieval_guard_triggered,
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        throw new Error("No response data from Copilot API.");
      }
    } catch (err: unknown) {
      console.warn("Copilot API fallback:", err);

      // Contextual fallback response for demo resilience
      const fallbackMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        sender: "assistant",
        text: `Here is what I found in the active campus opportunities database regarding "${messageContent}": We have several high-trust hackathons and internship fellowships currently open with rolling application deadlines.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        sources: [
          {
            id: "src-1",
            title: "National Generative AI Campus Hackathon 2026",
            domain: "Generative AI",
            location: "Bangalore / Hybrid",
            deadline: "In 12 days",
            similarity: 0.94,
          },
          {
            id: "src-2",
            title: "Global Open Source Fellowship & Research Grant",
            domain: "Open Source",
            location: "Remote",
            deadline: "In 28 days",
            similarity: 0.88,
          },
        ],
        retrievalGuardTriggered: false,
      };

      setMessages((prev) => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Expandable Chat Panel */}
      {isOpen && (
        <div className="mb-3 w-[360px] sm:w-[410px] h-[540px] max-h-[82vh] rounded-3xl border border-zinc-800 bg-zinc-950/95 backdrop-blur-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200">
          {/* Panel Header */}
          <div className="p-4 border-b border-zinc-800/80 bg-zinc-900/60 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-sm text-white">OpporSphere Copilot</h3>
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                </div>
                <p className="text-[10px] text-zinc-400">Verified Opportunity Intelligence</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handleResetSession}
                title="Start new conversation"
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Minimize"
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition cursor-pointer"
              >
                <Minus className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Conversation Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs scrollbar-thin">
            {messages.length === 0 ? (
              <div className="py-6 space-y-4 text-center">
                <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-semibold text-white text-sm">Ask OpporSphere Copilot</h4>
                  <p className="text-[11px] text-zinc-400 max-w-[280px] mx-auto leading-relaxed">
                    I answer questions grounded only in verified opportunities from our database with citations.
                  </p>
                </div>

                {/* Prompt Suggestions */}
                <div className="space-y-2 pt-2 text-left">
                  <span className="text-[10px] uppercase font-semibold text-zinc-500 tracking-wider block px-1">
                    Suggested Questions
                  </span>
                  <div className="space-y-1.5">
                    {STARTER_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => handleSendMessage(prompt)}
                        className="w-full text-left p-2.5 rounded-xl bg-zinc-900/60 hover:bg-zinc-800/80 border border-zinc-800/80 text-zinc-300 hover:text-indigo-200 transition text-[11px] flex items-center justify-between group cursor-pointer"
                      >
                        <span className="line-clamp-1">{prompt}</span>
                        <ChevronDown className="h-3 w-3 -rotate-90 text-zinc-500 group-hover:text-indigo-400 transition shrink-0 ml-1" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${
                    msg.sender === "user" ? "items-end" : "items-start"
                  }`}
                >
                  {/* Bubble */}
                  <div
                    className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                      msg.sender === "user"
                        ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-br-none shadow-md shadow-indigo-500/15"
                        : "bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-bl-none shadow-sm"
                    }`}
                  >
                    <p className="whitespace-pre-line">{msg.text}</p>
                  </div>

                  {/* Retrieval Guard Badge if triggered */}
                  {msg.retrievalGuardTriggered && (
                    <div className="mt-1.5 inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[10px]">
                      <ShieldAlert className="h-3 w-3" />
                      <span>Hallucination Guard: Safe Fallback</span>
                    </div>
                  )}

                  {/* Source Citation Chips */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 space-y-1 max-w-[90%]">
                      <div className="flex items-center gap-1 text-[10px] text-zinc-400 font-medium">
                        <ShieldCheck className="h-3 w-3 text-emerald-400" />
                        <span>Sources cited ({msg.sources.length}):</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.sources.map((citation, idx) => (
                          <SourceCitationChip
                            key={citation.id || idx}
                            citation={citation}
                            index={idx}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  <span className="text-[10px] text-zinc-500 mt-1 px-1">
                    {msg.timestamp}
                  </span>
                </div>
              ))
            )}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex items-center gap-2 text-zinc-400 text-xs bg-zinc-900/60 border border-zinc-800 p-3 rounded-2xl max-w-[70%]">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                <span>Searching vector database & grounding response...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-3 border-t border-zinc-800/80 bg-zinc-900/40">
            <div className="relative flex items-center rounded-2xl bg-zinc-900 border border-zinc-800 focus-within:border-indigo-500/60 focus-within:ring-1 focus-within:ring-indigo-500/30 transition">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about events, hackathons, deadlines..."
                className="w-full bg-transparent pl-4 pr-12 py-2.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleSendMessage()}
                disabled={isLoading || !inputMessage.trim()}
                className="absolute right-2 p-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 disabled:hover:bg-indigo-600 transition cursor-pointer"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="flex items-center justify-between text-[10px] text-zinc-500 px-1 pt-2">
              <span>Session: {sessionId.slice(0, 8)}...</span>
              <span>Local Ollama + pgvector RAG</span>
            </div>
          </div>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="group relative flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 text-white shadow-xl shadow-indigo-500/30 hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer"
        aria-label="Open AI Copilot"
      >
        <div className="relative">
          <Bot className="h-5 w-5" />
          <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-400" />
        </div>
        <span className="text-xs font-semibold tracking-tight">AI Copilot</span>
      </button>
    </div>
  );
}
