import React, { useState, useEffect, useRef } from 'react';
import { streamChat } from '../../api/chat';
import { Mic, Send, Bot, User, Check, Sparkles, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Chat = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        let agentMessage = { role: 'agent', content: '', agentName: 'Orchestrator' };
        setMessages(prev => [...prev, agentMessage]);

        await streamChat({
            message: userMessage.content,
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
            onDone: () => setIsTyping(false),
            onError: (err) => {
                console.error(err);
                setIsTyping(false);
            }
        });
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

    const DraftCard = ({ content, agentName }) => {
        // Simple heuristic to detect if content looks like structured data (e.g. list or JSON-ish)
        const isActionable = content.includes('-') || content.includes(':'); 

        return (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-4 mt-2">
                <div className="flex items-center gap-2 mb-2 text-xs font-bold uppercase tracking-wider text-white/50">
                    <Sparkles size={12} className="text-yellow-400" />
                    <span>{agentName} Draft</span>
                </div>
                <div className="prose prose-invert prose-sm max-w-none mb-4">
                     <p className="whitespace-pre-wrap text-white/80">{content}</p>
                </div>
                {isActionable && (
                    <button className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors text-sm w-full justify-center">
                        <Check size={16} />
                        Save to {agentName}
                    </button>
                )}
            </div>
        );
    };

    return (
        <div className="flex flex-col h-[calc(100vh-140px)]">
            <header className="mb-6">
                <h2 className="text-3xl font-bold text-white mb-1 font-display">Orchestrator</h2>
                <p className="text-white/60">Your AI command center.</p>
            </header>

            <div className="flex-1 overflow-y-auto pr-4 space-y-6 scrollbar-hide">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-white/20">
                        <Bot size={64} className="mb-4" />
                        <p>How can I help you today?</p>
                    </div>
                )}
                
                <AnimatePresence>
                    {messages.map((msg, idx) => (
                        <motion.div 
                            key={idx}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                                msg.role === 'user' ? 'bg-gradient-to-tr from-blue-500 to-purple-500' : 'bg-white/10'
                            }`}>
                                {msg.role === 'user' ? <User size={20} className="text-white" /> : <Bot size={20} className="text-white" />}
                            </div>
                            
                            <div className={`max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                                <div className="text-xs text-white/40 mb-1">
                                    {msg.role === 'user' ? 'You' : msg.agentName || 'Agent'}
                                </div>
                                
                                {msg.role === 'user' ? (
                                    <div className="bg-blue-600 text-white p-4 rounded-2xl rounded-tr-none inline-block text-left">
                                        {msg.content}
                                    </div>
                                ) : (
                                    <DraftCard content={msg.content} agentName={msg.agentName} />
                                )}
                            </div>
                        </motion.div>
                    ))}
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

            <div className="mt-4 relative">
                 <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none -top-20 h-20" />
                 <div className="relative flex items-center gap-2 bg-white/10 border border-white/10 p-2 rounded-full backdrop-blur-md">
                    <button 
                        onClick={toggleListening}
                        className={`p-3 rounded-full transition-all ${
                            isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-white/5 text-white/70 hover:bg-white/10 hover:text-white'
                        }`}
                    >
                        {isListening ? <div className="flex gap-1 h-5 items-center">
                            <span className="w-1 h-3 bg-white rounded-full animate-wave"></span>
                            <span className="w-1 h-5 bg-white rounded-full animate-wave delay-100"></span>
                            <span className="w-1 h-3 bg-white rounded-full animate-wave delay-200"></span>
                        </div> : <Mic size={20} />}
                    </button>
                    
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder-white/40 px-2"
                        placeholder="Type a message or press mic..."
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
