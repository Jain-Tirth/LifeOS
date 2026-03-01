import React, { useState } from "react";
import {
  Plus,
  MessageSquare,
  Trash2,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const SessionSwitcher = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const formatAgentType = (type) =>
    (type || "Chat")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase());

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  const handleDelete = (sessionId, e) => {
    e.stopPropagation();
    if (deleteConfirm === sessionId) {
      onDeleteSession(sessionId);
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(sessionId);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  return (
    <>
      {/* Toggle Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="absolute left-2 top-2 lg:-left-4 lg:-top-2 z-40 p-3 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/10 text-white transition-all shadow-lg"
        title={isOpen ? "Close sessions" : "Open sessions"}
      >
        {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </motion.button>

      {/* Sidebar */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            />

            {/* Sidebar Panel */}
            <motion.div
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed left-0 top-0 h-full w-80 bg-slate-900/95 backdrop-blur-xl border-r border-white/10 z-50 flex flex-col"
            >
              {/* Header */}
              <div className="p-4 border-b border-white/10">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-white">Sessions</h2>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-colors"
                  >
                    <X size={20} />
                  </button>
                </div>

                <button
                  onClick={() => {
                    onNewSession();
                    setIsOpen(false);
                  }}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-medium transition-all"
                >
                  <Plus size={18} />
                  New Session
                </button>
              </div>

              {/* Sessions List */}
              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {sessions.length === 0 ? (
                  <div className="text-center text-white/40 py-8">
                    <MessageSquare
                      size={48}
                      className="mx-auto mb-2 opacity-50"
                    />
                    <p>No sessions yet</p>
                  </div>
                ) : (
                  sessions.map((session) => (
                    <motion.div
                      key={session.session_id}
                      whileHover={{ scale: 1.02 }}
                      onClick={() => {
                        onSelectSession(session.session_id);
                        setIsOpen(false);
                      }}
                      className={`p-3 rounded-lg cursor-pointer transition-all group ${
                        currentSessionId === session.session_id
                          ? "bg-white/20 border border-white/30"
                          : "bg-white/5 hover:bg-white/10 border border-white/10"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <MessageSquare
                              size={14}
                              className="text-white/60 flex-shrink-0"
                            />
                            <span className="text-sm font-medium text-white truncate">
                              {formatAgentType(session.agent_type)}
                            </span>
                          </div>
                          <p className="text-xs text-white/40">
                            {formatDate(
                              session.updated_at || session.created_at,
                            )}
                          </p>
                          {session.message_count !== undefined && (
                            <p className="text-xs text-white/30 mt-1">
                              {session.message_count} messages
                            </p>
                          )}
                        </div>

                        <button
                          onClick={(e) => handleDelete(session.session_id, e)}
                          className={`p-1.5 rounded opacity-0 group-hover:opacity-100 transition-all ${
                            deleteConfirm === session.session_id
                              ? "bg-red-500 text-white"
                              : "hover:bg-white/10 text-white/60 hover:text-red-400"
                          }`}
                          title={
                            deleteConfirm === session.session_id
                              ? "Click again to confirm"
                              : "Delete session"
                          }
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default SessionSwitcher;
