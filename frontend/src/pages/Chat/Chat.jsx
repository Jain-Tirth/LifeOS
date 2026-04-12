/**
 * Chat — thin orchestrator shell.
 *
 * Sprint 3: Chat Monolith Decomposition
 * ──────────────────────────────────────
 * The original 400-line monolith has been decomposed into:
 *
 *   hooks/
 *     useChatState.js      — all useState/useRef declarations
 *     useSessionManager.js — session load / switch / delete
 *     useChatTransport.js  — streaming, send, speech recognition
 *
 *   components/
 *     ChatRenderer.jsx     — message list, empty state, typing indicator
 *     ChatInput.jsx        — input bar + mic button
 *
 * This file now acts as the thin wiring layer (~60 lines of logic).
 */
import React, { useEffect } from 'react';
import SessionSwitcher from '../../components/SessionSwitcher/SessionSwitcher';
import ScrollToBottom from '../../components/ScrollToBottom/ScrollToBottom';
import ChatRenderer from './components/ChatRenderer';
import ChatInput from './components/ChatInput';
import { useChatState } from './hooks/useChatState';
import { useSessionManager } from './hooks/useSessionManager';
import { useChatTransport } from './hooks/useChatTransport';


const Chat = () => {
    const state = useChatState();

    const {
        messages,
        input, setInput,
        isTyping, setIsTyping,
        isListening, setIsListening,
        sessionId, setSessionId,
        sessions, setSessions,
        loading, setLoading,
        showScrollButton, setShowScrollButton,
        savedItemsMap,
        messagesEndRef,
        inputRef,
        messagesContainerRef,
        historyLoadedRef,
        resetSession,
        markSaved,
        appendUserMessage,
        appendAgentPlaceholder,
        appendChunk,
        setLastMsgAgent,
        setLastMsgActions,
        deleteMessage,
        setMessages,
        setSavedItemsMap,
    } = state;

    // ─── Session management ────────────────────────────────────────────────
    const { handleNewSession, handleSelectSession, handleDeleteSession } = useSessionManager({
        sessionId,
        setSessionId,
        setSessions,
        setMessages,
        setLoading,
        setSavedItemsMap,
        resetSession,
        historyLoadedRef,
    });

    // ─── Transport layer ───────────────────────────────────────────────────
    const { handleSend, handleKeyPress, toggleListening } = useChatTransport({
        input,
        setInput,
        sessionId,
        setSessionId,
        setIsTyping,
        isListening,
        setIsListening,
        inputRef,
        setSessions,
        appendUserMessage,
        appendAgentPlaceholder,
        appendChunk,
        setLastMsgAgent,
        setLastMsgActions,
    });

    // ─── Scroll handling ───────────────────────────────────────────────────
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleScroll = () => {
        if (messagesContainerRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
            setShowScrollButton(
                scrollHeight - scrollTop - clientHeight > 200 && messages.length > 0
            );
        }
    };

    const scrollToBottom = () =>
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

    // ─── Render ────────────────────────────────────────────────────────────
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
                <h2 className="text-3xl font-bold text-white dark:text-white mb-1 ml-8 lg:ml-12 font-display">
                    Orchestrator
                </h2>
                <p className="text-white/60 text-sm sm:text-base ml-8 lg:ml-12">
                    Your AI command center — responses are auto-routed to the right agent.
                </p>
            </header>

            <ChatRenderer
                messages={messages}
                loading={loading}
                isTyping={isTyping}
                sessionId={sessionId}
                savedItemsMap={savedItemsMap}
                messagesEndRef={messagesEndRef}
                messagesContainerRef={messagesContainerRef}
                onScroll={handleScroll}
                onPromptSelect={(text) => {
                    setInput(text);
                    inputRef.current?.focus();
                }}
                onDeleteMsg={deleteMessage}
                onMarkSaved={markSaved}
            />

            <ScrollToBottom show={showScrollButton} onClick={scrollToBottom} />

            <ChatInput
                input={input}
                setInput={setInput}
                inputRef={inputRef}
                onSend={handleSend}
                onKeyPress={handleKeyPress}
                onToggleListen={toggleListening}
                isListening={isListening}
                disabled={isTyping}
            />
        </div>
    );
};

export default Chat;
