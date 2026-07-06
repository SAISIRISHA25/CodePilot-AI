import React, { useState, useEffect, useRef } from "react";
import { useProject } from "../contexts/ProjectContext";
import { queryService } from "../services/api";
import { Message, QuerySource } from "../types";
import { useToast } from "../contexts/ToastContext";
import {
  MessageSquare,
  Send,
  Loader2,
  Trash2,
  Copy,
  Check,
  FolderLock,
  ChevronDown,
  ChevronRight,
  Database,
  Plus,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export const AIChat: React.FC = () => {
  const { currentProject } = useProject();
  const { toast } = useToast();

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeSources, setActiveSources] = useState<Record<string, boolean>>({}); // msgId -> boolean to toggle sources
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Conversations list tracker
  const [conversations, setConversations] = useState<any[]>([
    { id: "conv-1", title: "General Project Q&A" },
  ]);
  const [activeConvId, setActiveConvId] = useState("conv-1");

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom on new messages
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Load chat messages when project or active conversation changes
  useEffect(() => {
    if (!currentProject) return;
    
    // Clear chat or load conversation logs from localStorage if present
    const saved = localStorage.getItem(`chat_history_${currentProject.id}_${activeConvId}`);
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch {
        setMessages([]);
      }
    } else {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: `Hi! I am your SDLC copilot for **${currentProject.name}**. Ask me questions, and I will search your vector indexed documents to answer with grounded references.`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    }
  }, [currentProject, activeConvId]);

  const saveHistory = (newMessages: Message[]) => {
    if (!currentProject) return;
    localStorage.setItem(
      `chat_history_${currentProject.id}_${activeConvId}`,
      JSON.stringify(newMessages)
    );
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentProject) return;
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Math.random().toString(36).substring(2, 9),
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    saveHistory(updatedMessages);
    setInput("");
    setIsLoading(true);

    try {
      // Call RAG Query Ask
      const reply = await queryService.ask(currentProject.id, userMessage.content);
      
      const assistantMessage: Message = {
        id: Math.random().toString(36).substring(2, 9),
        role: "assistant",
        content: reply.answer,
        timestamp: new Date().toLocaleTimeString(),
        sources: reply.sources,
      };

      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      saveHistory(finalMessages);
    } catch (error) {
      console.error(error);
      toast("Query execution failed.", "error");
      
      const errorMessage: Message = {
        id: Math.random().toString(36).substring(2, 9),
        role: "assistant",
        content: "Sorry, I encountered an error while retrieving context or generating an answer. Make sure you have uploaded and indexed reference documents in the Documents tab.",
        timestamp: new Date().toLocaleTimeString(),
      };
      const finalMessages = [...updatedMessages, errorMessage];
      setMessages(finalMessages);
      saveHistory(finalMessages);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast("Copied to clipboard", "success");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const clearChat = () => {
    if (!currentProject) return;

    const cleared = [
      {
        id: "welcome",
        role: "assistant",
        content: `Conversation cleared. How can I help you coordinate SDLC specs today?`,
        timestamp: new Date().toLocaleTimeString(),
      },
    ] as Message[];

    setMessages(cleared);
    saveHistory(cleared);
  };

  const toggleSources = (msgId: string) => {
    setActiveSources((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const createNewChat = () => {
    if (!currentProject) return;
    const newId = `conv-${Date.now()}`;
    const newConv = { id: newId, title: `Chat Session ${conversations.length + 1}` };
    setConversations([...conversations, newConv]);
    setActiveConvId(newId);
    toast("Created new chat session", "success");
  };

  if (!currentProject) {
    return (
      <div className="h-[80vh] flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto">
        <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
          <FolderLock className="w-8 h-8 text-blue-500" />
        </div>
        <h2 className="text-xl font-bold font-heading text-slate-100">Project Context Required</h2>
        <p className="text-sm text-slate-500 mt-2">
          Please select or create a project context from the dropdown at the top header to begin chatbot consultation.
        </p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-140px)] flex border border-slate-900 rounded-2xl overflow-hidden glass">
      {/* Chats sidebar Panel */}
      <aside className="w-64 border-r border-slate-900 bg-slate-950/40 hidden sm:flex flex-col">
        <div className="p-4 border-b border-slate-900 flex justify-between items-center">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
            Conversations
          </span>
          <button
            onClick={createNewChat}
            className="p-1 rounded-md hover:bg-slate-900 text-blue-400 hover:text-blue-300 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setActiveConvId(conv.id)}
              className={`w-full text-left px-3 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors ${
                activeConvId === conv.id
                  ? "bg-slate-900 text-blue-400"
                  : "text-slate-400 hover:bg-slate-900/40 hover:text-slate-200"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span className="truncate">{conv.title}</span>
            </button>
          ))}
        </div>
      </aside>

      {/* Main Chat Panel */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#07080d]/40">
        {/* Chat Header */}
        <header className="h-14 shrink-0 border-b border-slate-900 px-6 flex items-center justify-between bg-slate-950/20">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-blue-400" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Grounded AI Chat
            </h2>
          </div>

          <button
            onClick={clearChat}
            className="text-[11px] font-semibold text-red-400/80 hover:text-red-400 flex items-center gap-1 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Reset History</span>
          </button>
        </header>

        {/* Message logs */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => {
            const isUser = msg.role === "user";
            
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-4 ${isUser ? "justify-end" : "justify-start"}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shadow-md shrink-0">
                    AI
                  </div>
                )}

                <div className="flex flex-col max-w-[85%] md:max-w-[70%]">
                  <div
                    className={`p-4 rounded-2xl relative group ${
                      isUser
                        ? "bg-blue-600/90 text-white rounded-tr-sm"
                        : "bg-slate-900/60 border border-slate-800/60 text-slate-200 rounded-tl-sm"
                    }`}
                  >
                    {/* Message content */}
                    <p className="text-xs leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                    {/* Copy action */}
                    <button
                      onClick={() => copyToClipboard(msg.id, msg.content)}
                      className="absolute bottom-2 right-2 p-1 rounded bg-slate-950/60 text-slate-400 hover:text-slate-200 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      {copiedId === msg.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>

                  {/* Grounded sources badge accordion */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 text-[10px]">
                      <button
                        onClick={() => toggleSources(msg.id)}
                        className="flex items-center gap-1 text-slate-500 hover:text-slate-400 transition-colors font-semibold"
                      >
                        <Database className="w-3 h-3 text-blue-400" />
                        <span>Show Grounding Context ({msg.sources.length})</span>
                        {activeSources[msg.id] ? (
                          <ChevronDown className="w-3 h-3" />
                        ) : (
                          <ChevronRight className="w-3 h-3" />
                        )}
                      </button>

                      <AnimatePresence>
                        {activeSources[msg.id] && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden mt-1.5 space-y-1"
                          >
                            {msg.sources.map((src, sidx) => (
                              <div
                                key={sidx}
                                className="flex items-center justify-between p-2 rounded-lg border border-slate-900/60 bg-slate-950/30 text-[10px] text-slate-400"
                              >
                                <span className="font-medium truncate max-w-[180px]">{src.filename}</span>
                                <span className="font-mono text-slate-500 shrink-0">
                                  chunk {src.chunk_index} • rel: {(src.relevance_score * 100).toFixed(0)}%
                                </span>
                              </div>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}

                  <span className="text-[9px] text-slate-600 font-mono mt-1 self-start">
                    {msg.timestamp}
                  </span>
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300 text-xs font-bold shrink-0 border border-slate-700">
                    U
                  </div>
                )}
              </motion.div>
            );
          })}

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-4 justify-start"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shadow-md shrink-0">
                AI
              </div>
              <div className="flex items-center gap-2 p-4 rounded-2xl bg-slate-900/60 border border-slate-800/60 text-slate-500 text-xs">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-500" />
                <span>Reading vector sources context...</span>
              </div>
            </motion.div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input box form */}
        <form onSubmit={handleSend} className="p-4 border-t border-slate-900 bg-slate-950/20 flex gap-3">
          <input
            type="text"
            required
            disabled={isLoading}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about requirements, architecture specs..."
            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-900 bg-[#090b14] focus:border-blue-500 outline-none text-slate-200 text-xs transition-colors placeholder-slate-600 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center shrink-0 disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
