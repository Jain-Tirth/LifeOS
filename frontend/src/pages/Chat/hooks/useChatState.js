/**
 * useChatState — owns all chat UI state.
 * Extracted from Chat.jsx as part of Sprint 3: Chat Monolith Decomposition.
 */
import { useState, useRef } from 'react';

export function useChatState() {
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

    const resetSession = () => {
        setSessionId(null);
        setMessages([]);
        setSavedItemsMap({});
    };

    const markSaved = (msgIndex) =>
        setSavedItemsMap(prev => ({ ...prev, [msgIndex]: true }));

    const appendUserMessage = (content) => {
        const msg = { role: 'user', content, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, msg]);
        return msg;
    };

    const appendAgentPlaceholder = () => {
        const placeholder = { role: 'agent', content: '', agentName: 'Orchestrator', timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, placeholder]);
    };

    const appendChunk = (chunk) => {
        setMessages(prev => {
            const next = [...prev];
            const last = { ...next[next.length - 1] };
            last.content += chunk;
            next[next.length - 1] = last;
            return next;
        });
    };

    const setLastMsgAgent = (agentName, rawAgent) => {
        setMessages(prev => {
            const next = [...prev];
            const last = { ...next[next.length - 1] };
            last.agentName = agentName;
            last._rawAgent = rawAgent;
            return next;
        });
    };

    /** Attach an actionsApplied array to the most recent agent message */
    const setLastMsgActions = (actionsApplied) => {
        setMessages(prev => {
            const next = [...prev];
            // Walk backwards to find last agent message
            for (let i = next.length - 1; i >= 0; i--) {
                if (next[i].role === 'agent') {
                    next[i] = { ...next[i], actionsApplied };
                    break;
                }
            }
            return next;
        });
    };

    const deleteMessage = (index) =>
        setMessages(prev => prev.filter((_, i) => i !== index));

    return {
        // State
        messages, setMessages,
        input, setInput,
        isTyping, setIsTyping,
        isListening, setIsListening,
        sessionId, setSessionId,
        sessions, setSessions,
        loading, setLoading,
        showScrollButton, setShowScrollButton,
        savedItemsMap,

        // Refs
        messagesEndRef,
        inputRef,
        messagesContainerRef,
        historyLoadedRef,

        // Actions
        resetSession,
        markSaved,
        appendUserMessage,
        appendAgentPlaceholder,
        appendChunk,
        setLastMsgAgent,
        setLastMsgActions,
        deleteMessage,
    };
}
