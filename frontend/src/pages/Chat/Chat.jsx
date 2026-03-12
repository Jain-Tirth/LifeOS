import React, { useState, useEffect, useRef } from 'react';
import {
    streamChat,
    getSessions,
    getSessionMessages,
    deleteSession
} from '../../api/chat';
import { Mic, Bot, User, ArrowRight, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useToast } from '../../context/ToastContext';
import { useNavigate } from 'react-router-dom';
import MessageActions from '../../components/MessageActions/MessageActions';
import SessionSwitcher from '../../components/SessionSwitcher/SessionSwitcher';
import ScrollToBottom from '../../components/ScrollToBottom/ScrollToBottom';
import DraftCard from '../../components/DraftCard/DraftCard';
import { resolveAgentName } from '../../utils/agentParsers';
import { formatTimestamp, getDateSeparator } from '../../utils/timeFormatters';


// ─── Suggested Prompts ────────────────────────────────────────────────────────
const SUGGESTED_PROMPTS = [
    { label: 'Plan dinner', text: 'Plan a healthy dinner for tonight with easy ingredients' },
    { label: 'Organize tasks', text: 'Help me organize my tasks for this week' },
    { label: 'Study plan', text: 'Create a study plan for learning Data Structures' },
    { label: 'Wellness check', text: 'Suggest a 20-minute morning wellness routine' },
];


// ─── Main Component ───────────────────────────────────────────────────────────

const Chat = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [savedItemsMap, setSavedItemsMap] = useState({});
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const messagesContainerRef = useRef(null);
    const historyLoadedRef = useRef(false);
    const toast = useToast();
    const navigate = useNavigate();

    // ─── Scroll Handling ──────────────────────────────────────────────────
    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

    const handleScroll = () => {
        if (messagesContainerRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
            setShowScrollButton(scrollHeight - scrollTop - clientHeight > 200 && messages.length > 0);
        }
    };

    useEffect(() => { scrollToBottom(); }, [messages]);

    // ─── Load Chat History ────────────────────────────────────────────────
    useEffect(() => {
        const loadChatHistory = async () => {
            try {
                const sessionsResponse = await getSessions();
                const loadedSessions = sessionsResponse.data;
                setSessions(loadedSessions);

                if (loadedSessions?.length > 0) {
                    const lastSession = loadedSessions[0];
                    setSessionId(lastSession.session_id);

                    const messagesResponse = await getSessionMessages(lastSession.session_id);
                    const loadedMessages = messagesResponse.data.map(msg => ({
                        role: msg.role,
                        content: msg.content,
                        metadata: msg.metadata || null,
                        timestamp: msg.created_at || new Date().toISOString(),
                        agentName: msg.role === 'agent' ? resolveAgentName(msg) : null
                    }));
                    setMessages(loadedMessages);
                    if (loadedMessages.length > 0 && !historyLoadedRef.current) {
                        historyLoadedRef.current = true;
                        toast.success('Chat history loaded');
                    }
                }
            } catch (error) {
                console.error('Failed to load chat history:', error);
            } finally {
                setLoading(false);
            }
        };
        loadChatHistory();
    }, []);

    // ─── Session Management ───────────────────────────────────────────────
    const handleNewSession = () => {
        setSessionId(null);
        setMessages([]);
        setSavedItemsMap({});
    };

    const handleSelectSession = async (sid) => {
        try {
            setLoading(true);
            setSessionId(sid);
            setSavedItemsMap({});
            const messagesResponse = await getSessionMessages(sid);
            const loadedMessages = messagesResponse.data.map(msg => ({
                role: msg.role,
                content: msg.content,
                metadata: msg.metadata || null,
                timestamp: msg.created_at || new Date().toISOString(),
                agentName: msg.role === 'agent' ? resolveAgentName(msg) : null
            }));
            setMessages(loadedMessages);
        } catch (error) {
            console.error('Failed to load session:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteSession = async (sid) => {
        try {
            await deleteSession(sid);
        } catch (error) {
            if (error?.response?.status !== 404) {
                console.error('Failed to delete session from server:', error);
                toast.error('Could not delete session from server.');
                return;
            }
        }
        setSessions(prev => prev.filter(s => s.session_id !== sid));
        if (sid === sessionId) handleNewSession();
        toast.success('Session deleted');
    };

    // ─── Message Handling ─────────────────────────────────────────────────
    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        const agentMessage = { role: 'agent', content: '', agentName: 'Orchestrator', timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, agentMessage]);

        await streamChat({
            message: userMessage.content,
            sessionId,
            onChunk: (chunk) => {
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = { ...newMessages[newMessages.length - 1] };
                    lastMsg.content += chunk;
                    newMessages[newMessages.length - 1] = lastMsg;
                    return newMessages;
                });
            },
            onAgentSelected: (data) => {
                if (!sessionId && data.session_id) setSessionId(data.session_id);
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    lastMsg.agentName = data.agent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    lastMsg._rawAgent = data.agent;
                    return newMessages;
                });
            },
            onDone: async () => {
                setIsTyping(false);
                try {
                    const sessionsResponse = await getSessions();
                    setSessions(sessionsResponse.data);
                } catch (err) {
                    console.error('Failed to refresh sessions:', err);
                }
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

    // ─── Speech Recognition ───────────────────────────────────────────────
    const toggleListening = () => {
        if (!isListening) {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';
                recognition.onresult = (event) => {
                    setInput(prev => prev + event.results[0][0].transcript);
                    setIsListening(false);
                };
                recognition.onerror = () => { setIsListening(false); toast.error('Could not access microphone.'); };
                recognition.onend = () => setIsListening(false);
                recognition.start();
                setIsListening(true);
            } else {
                toast.error('Speech recognition is not supported in this browser.');
            }
        } else {
            setIsListening(false);
        }
    };

    // ─── Render ───────────────────────────────────────────────────────────
    return (
        <div className="flex flex-col h-full">
            <SessionSwitcher
                sessions={sessions}
                currentSessionId={sessionId}
                onSelectSession={handleSelectSession}
                onNewSession={handleNewSession}
                onDeleteSession={handleDeleteSession}
            />

            <header className="mb-6 pl-14 pt-2 lg:pl-0 lg:pt-0 block relative">
                <h2 className="text-3xl font-bold text-white dark:text-white mb-1 ml-8 lg:ml-12 font-display">Orchestrator</h2>
                <p className="text-white/60 text-sm sm:text-base ml-8 lg:ml-12">Your AI command center — responses are auto-routed to the right agent.</p>
            </header>

            <div
                ref={messagesContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto pr-4 space-y-6 scrollbar-hide scroll-gpu scroll-smooth"
            >
                {loading ? (
                    <div className="h-full flex flex-col items-center justify-center text-white/40">
                        <Loader2 size={48} className="mb-4 animate-spin" />
                        <p>Loading chat history...</p>
                    </div>
                ) : messages.length === 0 ? (
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
                                    onClick={() => { setInput(prompt.text); inputRef.current?.focus(); }}
                                    className="text-left p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all text-sm group"
                                >
                                    <span className="text-white/70 group-hover:text-white transition-colors">{prompt.label}</span>
                                    <p className="text-white/30 text-xs mt-1 truncate">{prompt.text}</p>
                                </motion.button>
                            ))}
                        </div>
                    </div>
                ) : null}

                <AnimatePresence>
                    {messages.map((msg, idx) => {
                        const dateSeparator = getDateSeparator(msg.timestamp, idx > 0 ? messages[idx - 1].timestamp : null);

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
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-gradient-to-tr from-blue-500 to-purple-500' : 'bg-white/10'}`}>
                                        {msg.role === 'user' ? <User size={20} className="text-white" /> : <Bot size={20} className="text-white" />}
                                    </div>

                                    <div className={`max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                                        <div className={`flex items-center gap-2 text-xs text-white/40 mb-1 ${msg.role === 'user' ? 'justify-end' : ''}`}>
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
                                                sessionId={sessionId}
                                                msgIndex={idx}
                                                isSaved={savedItemsMap[idx] || false}
                                                onMarkSaved={(i) => setSavedItemsMap(prev => ({ ...prev, [i]: true }))}
                                                onCopy={() => toast.success('Message copied')}
                                                onDelete={() => handleDeleteMessage(idx)}
                                                formatTimestamp={formatTimestamp}
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

            <ScrollToBottom show={showScrollButton} onClick={scrollToBottom} />

            <div className="mt-4 relative">
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none -top-20 h-20" />
                <div className="relative flex items-center gap-2 bg-white/10 border border-white/10 p-2 rounded-full backdrop-blur-md">
                    <button
                        onClick={toggleListening}
                        className={`p-3 rounded-full transition-all ${isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-white/5 text-white/70 hover:bg-white/10 hover:text-white'}`}
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
                        placeholder="Ask anything — I'll route it to the right agent..."
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
