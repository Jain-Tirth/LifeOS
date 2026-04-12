/**
 * useSessionManager — session CRUD and history loading logic.
 * Extracted from Chat.jsx as part of Sprint 3: Chat Monolith Decomposition.
 */
import { useEffect } from 'react';
import { getSessions, getSessionMessages, deleteSession } from '../../../api/chat';
import { resolveAgentName } from '../../../utils/agentParsers';
import { useToast } from '../../../context/ToastContext';

export function useSessionManager({
    sessionId,
    setSessionId,
    setSessions,
    setMessages,
    setLoading,
    setSavedItemsMap,
    resetSession,
    historyLoadedRef,
}) {
    const toast = useToast();

    // Load latest session on mount
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
                    const loadedMessages = _mapMessages(messagesResponse.data);
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
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleNewSession = () => {
        resetSession();
    };

    const handleSelectSession = async (sid) => {
        try {
            setLoading(true);
            setSessionId(sid);
            setSavedItemsMap({});
            const messagesResponse = await getSessionMessages(sid);
            setMessages(_mapMessages(messagesResponse.data));
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
        if (sid === sessionId) resetSession();
        toast.success('Session deleted');
    };

    return { handleNewSession, handleSelectSession, handleDeleteSession };
}

// ─── Private ──────────────────────────────────────────────────────────────────

function _mapMessages(rawMessages) {
    return rawMessages.map(msg => ({
        role: msg.role,
        content: msg.content,
        metadata: msg.metadata || null,
        timestamp: msg.created_at || new Date().toISOString(),
        agentName: msg.role === 'agent' ? resolveAgentName(msg) : null,
        actionsApplied: msg.metadata?.actions_applied || null,
    }));
}
