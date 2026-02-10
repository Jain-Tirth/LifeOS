import client from './client';

// Helper to get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

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
        // Prepare headers
        const headers = {
            'Content-Type': 'application/json',
        };
        
        // Add JWT token if available
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Add CSRF token for session authentication
        const csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch('/api/chat/stream/', {
            method: 'POST',
            headers: headers,
            credentials: 'include', // Important for session auth
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
                        console.log('[STREAM] Parsed data:', data);
                        
                        if (data.type === 'agent_selected' && onAgentSelected) {
                            onAgentSelected(data);
                        } else if (data.type === 'chunk' && onChunk) {
                            console.log('[STREAM] Chunk content:', data.content);
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

// Agent-specific save functions
export const saveMealPlan = async (mealPlanData) => {
    return client.post('/meal-plans/', mealPlanData);
};

export const saveTask = async (taskData) => {
    return client.post('/tasks/', taskData);
};

export const saveStudySession = async (studySessionData) => {
    return client.post('/study-sessions/', studySessionData);
};

export const saveWellnessActivity = async (activityData) => {
    return client.post('/wellness-activities/', activityData);
};
