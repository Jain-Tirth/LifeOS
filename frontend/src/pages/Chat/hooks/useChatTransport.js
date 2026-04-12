/**
 * useChatTransport — handles streaming, sending, speech recognition.
 * Extracted from Chat.jsx as part of Sprint 3: Chat Monolith Decomposition.
 */
import { streamChat, getSessions } from '../../../api/chat';
import { useToast } from '../../../context/ToastContext';

export function useChatTransport({
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
}) {
    const toast = useToast();

    const handleSend = async () => {
        if (!input.trim()) return;

        const content = input;
        setInput('');
        appendUserMessage(content);
        setIsTyping(true);
        appendAgentPlaceholder();

        await streamChat({
            message: content,
            sessionId,
            onChunk: (chunk) => appendChunk(chunk),
            onAgentSelected: (data) => {
                if (!sessionId && data.session_id) setSessionId(data.session_id);
                const agentName = data.agent
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, l => l.toUpperCase());
                setLastMsgAgent(agentName, data.agent);
            },
            onActionsApplied: (actions) => {
                setLastMsgActions(actions);
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
            },
        });
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const toggleListening = () => {
        if (!isListening) {
            const SpeechRecognition =
                window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';
                recognition.onresult = (event) => {
                    setInput(prev => prev + event.results[0][0].transcript);
                    setIsListening(false);
                };
                recognition.onerror = () => {
                    setIsListening(false);
                    toast.error('Could not access microphone.');
                };
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

    return { handleSend, handleKeyPress, toggleListening };
}
