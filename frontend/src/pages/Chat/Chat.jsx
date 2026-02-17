import React, { useState, useEffect, useRef } from 'react';
import {
    streamChat,
    getSessions,
    getSessionMessages,
    saveMealPlan,
    saveTask,
    saveStudySession,
    saveWellnessActivity
} from '../../api/chat';
import { Mic, Send, Bot, User, Check, Sparkles, ArrowRight, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useToast } from '../../context/ToastContext';
import MessageActions from '../../components/MessageActions/MessageActions';
import SessionSwitcher from '../../components/SessionSwitcher/SessionSwitcher';
import ScrollToBottom from '../../components/ScrollToBottom/ScrollToBottom';

const Chat = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const messagesContainerRef = useRef(null);
    const toast = useToast();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    // Handle scroll to show/hide scroll button
    const handleScroll = () => {
        if (messagesContainerRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
            const isNearBottom = scrollHeight - scrollTop - clientHeight < 200;
            setShowScrollButton(!isNearBottom && messages.length > 0);
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load chat history on mount
    useEffect(() => {
        const loadChatHistory = async () => {
            try {
                // Get user sessions
                const sessionsResponse = await getSessions();
                const loadedSessions = sessionsResponse.data;
                setSessions(loadedSessions);

                if (loadedSessions && loadedSessions.length > 0) {
                    // Get the most recent session
                    const lastSession = loadedSessions[0];
                    setSessionId(lastSession.session_id);

                    // Load messages for this session
                    const messagesResponse = await getSessionMessages(lastSession.session_id);
                    const loadedMessages = messagesResponse.data.map(msg => ({
                        role: msg.role,
                        content: msg.content,
                        timestamp: msg.timestamp || new Date().toISOString(),
                        agentName: msg.role === 'agent' ? 'Agent' : null
                    }));
                    setMessages(loadedMessages);
                    toast.success('Chat history loaded');
                }
            } catch (error) {
                console.error('Failed to load chat history:', error);
            } finally {
                setLoading(false);
            }
        };

        loadChatHistory();
    }, []);

    const handleNewSession = () => {
        setSessionId(null);
        setMessages([]);
    };

    const handleSelectSession = async (sid) => {
        try {
            setLoading(true);
            setSessionId(sid);
            const messagesResponse = await getSessionMessages(sid);
            const loadedMessages = messagesResponse.data.map(msg => ({
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp || new Date().toISOString(),
                agentName: msg.role === 'agent' ? 'Agent' : null
            }));
            setMessages(loadedMessages);
        } catch (error) {
            console.error('Failed to load session:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteSession = async (sid) => {
        // Note: This is frontend-only deletion, no backend call
        setSessions(prev => prev.filter(s => s.session_id !== sid));
        if (sid === sessionId) {
            handleNewSession();
        }
        toast.success('Session deleted');
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = {
            role: 'user',
            content: input,
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        let agentMessage = {
            role: 'agent',
            content: '',
            agentName: 'Orchestrator',
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, agentMessage]);

        await streamChat({
            message: userMessage.content,
            sessionId: sessionId,
            onChunk: (chunk) => {
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    lastMsg.content += chunk;
                    return newMessages;
                });
            },
            onAgentSelected: (data) => {
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    lastMsg.agentName = data.agent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                    return newMessages;
                });
            },
            onDone: () => {
                setIsTyping(false);
            },
            onError: (err) => {
                console.error(err);
                setIsTyping(false);
                toast.error('Failed to send message. Please try again.');
            }
        });
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleDeleteMessage = (index) => {
        setMessages(prev => prev.filter((_, i) => i !== index));
    };

    const handleRegenerateResponse = async (index) => {
        // Find the user message before this agent response
        const userMessageIndex = index - 1;
        if (userMessageIndex >= 0 && messages[userMessageIndex].role === 'user') {
            // Remove the current agent response
            setMessages(prev => prev.filter((_, i) => i !== index));
            // Resend the user message
            const userContent = messages[userMessageIndex].content;
            setInput(userContent);
        }
    };

    // Placeholder for Speech-to-Text
    const toggleListening = () => {
        if (!isListening) {
            setIsListening(true);
            // Simulate listening
            setTimeout(() => {
                setInput("Plan a healthy meal for dinner.");
                setIsListening(false);
            }, 2000);
        } else {
            setIsListening(false);
        }
    };

    const formatTimestamp = (timestamp) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    };

    // Group messages by date
    const getDateSeparator = (currentTimestamp, prevTimestamp) => {
        if (!prevTimestamp) return 'Today';

        const current = new Date(currentTimestamp);
        const prev = new Date(prevTimestamp);

        const currentDate = current.toDateString();
        const prevDate = prev.toDateString();

        if (currentDate !== prevDate) {
            const today = new Date().toDateString();
            const yesterday = new Date(Date.now() - 86400000).toDateString();

            if (currentDate === today) return 'Today';
            if (currentDate === yesterday) return 'Yesterday';
            return current.toLocaleDateString();
        }

        return null;
    };

    const DraftCard = ({ content, agentName, timestamp, onCopy, onDelete }) => {
        // Simple heuristic to detect if content looks like structured data (e.g. list or JSON-ish)
        const isActionable = content.includes('-') || content.includes(':');
        const [saving, setSaving] = useState(false);
        const [saved, setSaved] = useState(false);

        // Helper to extract title from content (first line or first heading)
        const extractTitle = (text) => {
            const lines = text.split('\n');
            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith('#')) {
                    return trimmed.replace(/^#+\s*/, '');
                }
                if (trimmed.length > 0 && trimmed.length < 200) {
                    return trimmed;
                }
            }
            return null;
        };

        const handleSave = async () => {
            setSaving(true);
            try {
                // Determine the agent type
                const agentType = agentName.toLowerCase().replace(/\s+/g, '_');

                // Parse content and save based on agent type
                let saveResult;

                if (agentType.includes('meal') || agentType.includes('planner')) {
                    // Parse meal plan from content
                    const mealPlanData = {
                        date: new Date().toISOString().split('T')[0],
                        meal_type: 'dinner',
                        meal_name: extractTitle(content) || 'Generated Meal Plan',
                        instructions: content
                    };
                    saveResult = await saveMealPlan(mealPlanData);
                } else if (agentType.includes('productivity') || agentType.includes('task')) {
                    // Parse task from content
                    const taskData = {
                        title: extractTitle(content) || 'Generated Task',
                        description: content,
                        priority: 'medium',
                        status: 'todo'
                    };
                    saveResult = await saveTask(taskData);
                } else if (agentType.includes('study') || agentType.includes('buddy')) {
                    // Parse study session from content
                    const studyData = {
                        subject: extractTitle(content) || 'Study Session',
                        duration: 60,
                        notes: content
                    };
                    saveResult = await saveStudySession(studyData);
                } else if (agentType.includes('wellness')) {
                    // Parse wellness activity from content
                    const activityData = {
                        activity_type: 'exercise',
                        notes: content,
                        recorded_at: new Date().toISOString()
                    };
                    saveResult = await saveWellnessActivity(activityData);
                } else {
                    throw new Error('Unknown agent type');
                }

                console.log('Saved successfully:', saveResult);
                setSaved(true);
                toast.success(`Saved to ${agentName}`);
                setTimeout(() => setSaved(false), 3000);
            } catch (error) {
                console.error('Failed to save:', error);
                toast.error('Failed to save content. Please try again.');
            } finally {
                setSaving(false);
            }
        };

        return (
            <div className="bg-white/5 dark:bg-white/5 border border-white/10 dark:border-white/10 rounded-2xl p-5 mt-2 group">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white/50">
                        <Sparkles size={12} className="text-yellow-400" />
                        <span>{agentName}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-white/30">{formatTimestamp(timestamp)}</span>
                        <MessageActions
                            message={content}
                            onCopy={onCopy}
                            onDelete={onDelete}
                        />
                    </div>
                </div>
                <div className="prose prose-invert prose-sm max-w-none mb-4 text-white/90 leading-relaxed">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            h1: ({ children }) => <h1 className="text-2xl font-bold text-white mb-3 mt-4">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-xl font-bold text-white mb-2 mt-3">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-lg font-semibold text-white mb-2 mt-2">{children}</h3>,
                            p: ({ children }) => <p className="text-white/80 mb-2">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1 text-white/80">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1 text-white/80">{children}</ol>,
                            li: ({ children }) => <li className="text-white/80 ml-2">{children}</li>,
                            code: ({ inline, children }) =>
                                inline ?
                                    <code className="bg-white/10 px-1.5 py-0.5 rounded text-sm font-mono text-yellow-300">{children}</code> :
                                    <code className="block bg-white/10 p-3 rounded-lg text-sm font-mono text-yellow-300 my-2 overflow-x-auto">{children}</code>,
                            strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
                            em: ({ children }) => <em className="italic text-white/90">{children}</em>,
                            blockquote: ({ children }) => <blockquote className="border-l-4 border-purple-400 pl-4 italic text-white/70 my-2">{children}</blockquote>,
                        }}
                    >
                        {content}
                    </ReactMarkdown>
                </div>
                {isActionable && (
                    <button
                        onClick={handleSave}
                        disabled={saving || saved}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm w-full justify-center ${saved
                            ? 'bg-green-500/20 text-green-300 border border-green-500/50'
                            : 'bg-white/10 hover:bg-white/20 text-white border border-white/10'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                        {saving ? (
                            <>
                                <Loader2 size={16} className="animate-spin" />
                                Saving...
                            </>
                        ) : saved ? (
                            <>
                                <Check size={16} />
                                Saved to {agentName}
                            </>
                        ) : (
                            <>
                                <Check size={16} />
                                Save to {agentName}
                            </>
                        )}
                    </button>
                )}
            </div>
        );
    };

    return (
        <div className="flex flex-col h-[calc(100vh-140px)]">
            {/* Session Switcher */}
            <SessionSwitcher
                sessions={sessions}
                currentSessionId={sessionId}
                onSelectSession={handleSelectSession}
                onNewSession={handleNewSession}
                onDeleteSession={handleDeleteSession}
            />

            <header className="mb-6">
                <h2 className="text-3xl font-bold text-white dark:text-white mb-1 font-display">Orchestrator</h2>
                <p className="text-white/60">Your AI command center.</p>
            </header>

            <div
                ref={messagesContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto pr-4 space-y-6 scrollbar-hide"
            >
                {loading ? (
                    <div className="h-full flex flex-col items-center justify-center text-white/40">
                        <Loader2 size={48} className="mb-4 animate-spin" />
                        <p>Loading chat history...</p>
                    </div>
                ) : messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-white/20">
                        <Bot size={64} className="mb-4" />
                        <p>How can I help you today?</p>
                    </div>
                ) : null}

                <AnimatePresence>
                    {messages.map((msg, idx) => {
                        const dateSeparator = getDateSeparator(
                            msg.timestamp,
                            idx > 0 ? messages[idx - 1].timestamp : null
                        );

                        return (
                            <React.Fragment key={idx}>
                                {dateSeparator && (
                                    <div className="flex items-center gap-4 my-6">
                                        <div className="flex-1 h-px bg-white/10"></div>
                                        <span className="text-xs text-white/30 font-medium">{dateSeparator}</span>
                                        <div className="flex-1 h-px bg-white/10"></div>
                                    </div>
                                )}

                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                                >
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-gradient-to-tr from-blue-500 to-purple-500' : 'bg-white/10'
                                        }`}>
                                        {msg.role === 'user' ? <User size={20} className="text-white" /> : <Bot size={20} className="text-white" />}
                                    </div>

                                    <div className={`max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                                        <div className="flex items-center gap-2 text-xs text-white/40 mb-1 ${msg.role === 'user' ? 'justify-end' : ''}">
                                            <span>{msg.role === 'user' ? 'You' : msg.agentName || 'Agent'}</span>
                                            <span>•</span>
                                            <span>{formatTimestamp(msg.timestamp)}</span>
                                        </div>

                                        {msg.role === 'user' ? (
                                            <div className="group">
                                                <div className="bg-blue-600 text-white p-4 rounded-2xl rounded-tr-none inline-block text-left relative">
                                                    {msg.content}
                                                </div>
                                                <div className="mt-1 flex justify-end">
                                                    <MessageActions
                                                        message={msg.content}
                                                        onCopy={() => toast.success('Message copied')}
                                                        onDelete={() => handleDeleteMessage(idx)}
                                                    />
                                                </div>
                                            </div>
                                        ) : (
                                            <DraftCard
                                                content={msg.content}
                                                agentName={msg.agentName}
                                                timestamp={msg.timestamp}
                                                onCopy={() => toast.success('Message copied')}
                                                onDelete={() => handleDeleteMessage(idx)}
                                            />
                                        )}
                                    </div>
                                </motion.div>
                            </React.Fragment>
                        );
                    })}
                </AnimatePresence>

                {isTyping && (
                    <div className="flex gap-4">
                        <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                            <Bot size={20} className="text-white" />
                        </div>
                        <div className="flex gap-1 items-center h-10 px-4 bg-white/5 rounded-2xl">
                            <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce"></span>
                            <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce delay-100"></span>
                            <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce delay-200"></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Scroll to Bottom Button */}
            <ScrollToBottom show={showScrollButton} onClick={scrollToBottom} />

            <div className="mt-4 relative">
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none -top-20 h-20" />
                <div className="relative flex items-center gap-2 bg-white/10 border border-white/10 p-2 rounded-full backdrop-blur-md">
                    <button
                        onClick={toggleListening}
                        className={`p-3 rounded-full transition-all ${isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-white/5 text-white/70 hover:bg-white/10 hover:text-white'
                            }`}
                    >
                        {isListening ? <div className="flex gap-1 h-5 items-center">
                            <span className="w-1 h-3 bg-white rounded-full animate-wave"></span>
                            <span className="w-1 h-5 bg-white rounded-full animate-wave delay-100"></span>
                            <span className="w-1 h-3 bg-white rounded-full animate-wave delay-200"></span>
                        </div> : <Mic size={20} />}
                    </button>

                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyPress}
                        className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder-white/40 px-2 resize-none max-h-32 min-h-[24px] overflow-y-auto"
                        placeholder="Type a message (Shift+Enter for newline)..."
                        rows={1}
                        style={{ height: 'auto' }}
                        onInput={(e) => {
                            e.target.style.height = 'auto';
                            e.target.style.height = e.target.scrollHeight + 'px';
                        }}
                    />

                    <button
                        onClick={handleSend}
                        disabled={!input.trim()}
                        className="p-3 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-full text-white disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform"
                    >
                        <ArrowRight size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Chat;
