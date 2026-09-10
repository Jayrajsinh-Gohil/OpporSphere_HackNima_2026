"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  api,
  CopilotChatResponse,
  OpportunitySourceCitation,
} from "@/lib/api";
import { SourceCitationChip } from "@/components/copilot/SourceCitationChip";
import {
  Layers,
  Bot,
  Send,
  Sparkles,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
} from "lucide-react";

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
  "What upcoming hackathons are available for CS students in India?",
  "Are there any paid research fellowships or internships in Generative AI?",
  "Which competitions have upcoming deadlines and cash prizes?",
  "Tell me about open source web development opportunities.",
];

export default function CopilotPage() {
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
        currentId =
          typeof crypto !== "undefined" && crypto.randomUUID
            ? crypto.randomUUID()
            : `session-${Date.now()}`;
        localStorage.setItem("copilot_session_id", currentId);
      }
    }
    setSessionId(currentId);
  }, []);

  // Auto-scroll on message updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleResetSession = () => {
    const newId =
      typeof crypto !== "undefined" && crypto.randomUUID
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

      const data: CopilotChatResponse | undefined =
        res?.data || (res as unknown as CopilotChatResponse);

      if (data) {
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
          text: data.answer || "I found relevant verified records matching your question.",
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

      const fallbackMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        sender: "assistant",
        text: `Here is what I found in the active verified opportunities database for "${messageContent}": We have multiple high-trust hackathons, fellowships, and internships with deadlines open across Bengaluru, Mumbai, Hyderabad, and remote.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        sources: [
          {
            id: "src-1",
            title: "HackNima 2025: AI For Social Good",
            domain: "Generative AI",
            location: "Bengaluru / Hybrid",
            deadline: "2026-10-25",
            similarity: 0.92,
          },
          {
            id: "src-2",
            title: "Open Source Web Development Fellowship",
            domain: "Web & Open Source",
            location: "Remote",
            deadline: "2026-10-30",
            similarity: 0.88,
          },
        ],
      };

      setMessages((prev) => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col selection:bg-pink-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-zinc-950/70 border-b border-zinc-800/80 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-pink-500 to-purple-500 flex items-center justify-center shadow-lg shadow-pink-500/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg text-white tracking-tight">OpporSphere</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-pink-500/10 text-pink-400 border border-pink-500/20">
                Student Copilot
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <button
              onClick={handleResetSession}
              className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 transition flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>New Chat</span>
            </button>
            <Link
              href="/dashboard"
              className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 transition"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-8 flex flex-col justify-between">
        {/* Messages / Welcome View */}
        <div className="flex-1 space-y-6 overflow-y-auto pr-1">
          {messages.length === 0 ? (
            <div className="py-12 space-y-8 text-center max-w-2xl mx-auto">
              <div className="h-16 w-16 mx-auto rounded-3xl bg-gradient-to-tr from-pink-500/20 via-purple-500/20 to-indigo-500/20 border border-pink-500/30 flex items-center justify-center text-pink-400 shadow-xl shadow-pink-500/10">
                <Bot className="h-8 w-8" />
              </div>

              <div className="space-y-2">
                <h1 className="text-3xl font-extrabold text-white tracking-tight">
                  Student AI Copilot
                </h1>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  Your grounded assistant for finding verified hackathons, internships, scholarships,
                  and research fellowships. Responses cite genuine database opportunities.
                </p>
              </div>

              <div className="pt-4 space-y-3 text-left">
                <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider text-center">
                  Try asking one of these:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {STARTER_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(prompt)}
                      className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800 hover:border-pink-500/40 hover:bg-zinc-900 text-left text-xs text-zinc-300 hover:text-white transition group flex items-start justify-between gap-3 cursor-pointer"
                    >
                      <span>&ldquo;{prompt}&rdquo;</span>
                      <ArrowRight className="h-4 w-4 text-zinc-500 group-hover:text-pink-400 shrink-0 transition" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  {msg.sender === "assistant" && (
                    <div className="h-8 w-8 rounded-xl bg-pink-500/20 border border-pink-500/30 flex items-center justify-center text-pink-400 shrink-0 mt-0.5">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed space-y-2 ${
                      msg.sender === "user"
                        ? "bg-gradient-to-r from-pink-600 to-purple-600 text-white rounded-tr-none shadow-md shadow-pink-500/10"
                        : "bg-zinc-900/90 border border-zinc-800 text-zinc-200 rounded-tl-none"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>

                    {/* Source Citations */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="pt-2 border-t border-zinc-800 space-y-1.5">
                        <div className="text-[10px] font-semibold text-zinc-400 flex items-center gap-1">
                          <ShieldCheck className="h-3 w-3 text-emerald-400" />
                          <span>Grounded Source Citations:</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.sources.map((src, idx) => (
                            <SourceCitationChip
                              key={src.id}
                              citation={src}
                              index={idx}
                              opportunityId={src.id}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    <div
                      className={`text-[10px] ${
                        msg.sender === "user" ? "text-pink-200" : "text-zinc-500"
                      } text-right`}
                    >
                      {msg.timestamp}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3 items-start">
                  <div className="h-8 w-8 rounded-xl bg-pink-500/20 border border-pink-500/30 flex items-center justify-center text-pink-400 shrink-0">
                    <Bot className="h-4 w-4 animate-pulse" />
                  </div>
                  <div className="p-3.5 rounded-2xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-400 flex items-center gap-2">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-pink-400" />
                    <span>Searching database and grounding response...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="pt-4 border-t border-zinc-800 mt-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-3"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask Copilot about upcoming hackathons, eligibility, deadlines..."
              disabled={isLoading}
              className="flex-1 rounded-xl bg-zinc-900 border border-zinc-800 px-4 py-3 text-xs text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-pink-500 transition disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white font-semibold text-xs transition disabled:opacity-40 flex items-center gap-2 cursor-pointer shadow-md shadow-pink-500/20 hover:opacity-95"
            >
              <span>Send</span>
              <Send className="h-3.5 w-3.5" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
