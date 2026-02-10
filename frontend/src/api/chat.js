import client from './client';

export const sendMessage = async (message, sessionId = null, forceAgent = null) => {
    return client.post('/chat/', {
        message,
        session_id: sessionId,
        force_agent: forceAgent,
    });
};

export const streamChat = async ({ message, sessionId, onChunk, onAgentSelected, onError, onDone }) => {
    const token = localStorage.getItem('lifeos_token');
    
    try {
        const response = await fetch('/api/chat/stream/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                if (onDone) onDone();
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'agent_selected' && onAgentSelected) {
                            onAgentSelected(data);
                        } else if (data.type === 'chunk' && onChunk) {
                            onChunk(data.content);
                        } else if (data.type === 'error' && onError) {
                            onError(data.error);
                        } else if (data.type === 'done' && onDone) {
                            onDone();
                            return; // Stop processing
                        }
                    } catch (e) {
                        console.error('JSON parse error:', e, 'Line:', line);
                    }
                }
            }
        }
    } catch (error) {
        if (onError) onError(error.message);
    }
};

export const getSessions = async () => {
    return client.get('/my-sessions/');
};

export const getSessionMessages = async (sessionId) => {
    return client.get(`/sessions/${sessionId}/messages/`);
};
