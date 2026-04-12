/**
 * ChatRenderer — message list renderer.
 * Sprint 3: Chat Monolith Decomposition.
 *
 * Owns:
 *   - Empty state (suggested prompts)
 *   - Loading state
 *   - Date separators
 *   - User messages
 *   - Agent messages via DraftCard (which uses AgentOutputRenderer + ActionFeedbackBanner)
 *   - Typing indicator
 */
import React from 'react';
import { Bot, User, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import DraftCard from '../../../components/DraftCard/DraftCard';
import MessageActions from '../../../components/MessageActions/MessageActions';
import { formatTimestamp, getDateSeparator } from '../../../utils/timeFormatters';
import { useToast } from '../../../context/ToastContext';

const SUGGESTED_PROMPTS = [
    { label: 'Plan dinner', text: 'Plan a healthy dinner for tonight with easy ingredients' },
    { label: 'Organize tasks', text: 'Help me organize my tasks for this week' },
    { label: 'Study plan', text: 'Create a study plan for learning Data Structures' },
    { label: 'Wellness check', text: 'Suggest a 20-minute morning wellness routine' },
];

const ChatRenderer = ({
    messages,
    loading,
    isTyping,
    sessionId,
    savedItemsMap,
    messagesEndRef,
    messagesContainerRef,
    onScroll,
    onPromptSelect,
    onDeleteMsg,
    onMarkSaved,
}) => {
    const toast = useToast();

    return (
        <div
            ref={messagesContainerRef}
            onScroll={onScroll}
            className="flex-1 overflow-y-auto pr-4 space-y-6 scrollbar-hide scroll-gpu scroll-smooth"
        >
            {/* Loading state */}
            {loading && (
                <div className="h-full flex flex-col items-center justify-center text-white/40">
                    <Loader2 size={48} className="mb-4 animate-spin" />
                    <p>Loading chat history...</p>
                </div>
            )}

            {/* Empty state */}
            {!loading && messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center">
                    <div className="relative mb-8">
                        <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/30 to-purple-500/30 rounded-full blur-2xl scale-150" />
                        <Bot size={64} className="text-white/30 relative" />
                    </div>
                    <p className="text-white/40 text-lg mb-8">How can I help you today?</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
                        {SUGGESTED_PROMPTS.map((prompt, i) => (
                            <motion.button
                                key={i}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 }}
                                onClick={() => onPromptSelect(prompt.text)}
                                className="text-left p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all text-sm group"
                            >
                                <span className="text-white/70 group-hover:text-white transition-colors">{prompt.label}</span>
                                <p className="text-white/30 text-xs mt-1 truncate">{prompt.text}</p>
                            </motion.button>
                        ))}
                    </div>
                </div>
            )}

            {/* Message list */}
            <AnimatePresence>
                {messages.map((msg, idx) => {
                    const dateSeparator = getDateSeparator(
                        msg.timestamp,
                        idx > 0 ? messages[idx - 1].timestamp : null
                    );

                    return (
                        <React.Fragment key={idx}>
                            {/* Date separator */}
                            {dateSeparator && (
                                <div className="flex items-center gap-4 my-6">
                                    <div className="flex-1 h-px bg-white/10" />
                                    <span className="text-xs text-white/30 font-medium">{dateSeparator}</span>
                                    <div className="flex-1 h-px bg-white/10" />
                                </div>
                            )}

                            {/* Message bubble */}
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                            >
                                {/* Avatar */}
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user'
                                    ? 'bg-gradient-to-tr from-blue-500 to-purple-500'
                                    : 'bg-white/10'
                                    }`}>
                                    {msg.role === 'user'
                                        ? <User size={20} className="text-white" />
                                        : <Bot size={20} className="text-white" />
                                    }
                                </div>

                                {/* Content */}
                                <div className={`max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                                    {/* Name + time */}
                                    <div className={`flex items-center gap-2 text-xs text-white/40 mb-1 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                                        <span>{msg.role === 'user' ? 'You' : msg.agentName || 'Agent'}</span>
                                        <span>•</span>
                                        <span>{formatTimestamp(msg.timestamp)}</span>
                                    </div>

                                    {/* User message */}
                                    {msg.role === 'user' ? (
                                        <div className="group">
                                            <div className="bg-blue-600 text-white p-4 rounded-2xl rounded-tr-none inline-block text-left relative">
                                                {msg.content}
                                            </div>
                                            <div className="mt-1 flex justify-end">
                                                <MessageActions
                                                    message={msg.content}
                                                    onCopy={() => toast.success('Message copied')}
                                                    onDelete={() => onDeleteMsg(idx)}
                                                />
                                            </div>
                                        </div>
                                    ) : (
                                        /* Agent message via DraftCard */
                                        <DraftCard
                                            content={msg.content}
                                            agentName={msg.agentName}
                                            timestamp={msg.timestamp}
                                            sessionId={sessionId}
                                            msgIndex={idx}
                                            isSaved={savedItemsMap[idx] || false}
                                            actionsApplied={msg.actionsApplied || null}
                                            onMarkSaved={onMarkSaved}
                                            onCopy={() => toast.success('Message copied')}
                                            onDelete={() => onDeleteMsg(idx)}
                                            formatTimestamp={formatTimestamp}
                                        />
                                    )}
                                </div>
                            </motion.div>
                        </React.Fragment>
                    );
                })}
            </AnimatePresence>

            {/* Typing indicator */}
            {isTyping && (
                <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                        <Bot size={20} className="text-white" />
                    </div>
                    <div className="flex gap-1 items-center h-10 px-4 bg-white/5 rounded-2xl">
                        <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce" />
                        <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce delay-100" />
                        <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce delay-200" />
                    </div>
                </div>
            )}

            <div ref={messagesEndRef} />
        </div>
    );
};

export default ChatRenderer;
