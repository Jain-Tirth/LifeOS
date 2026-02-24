import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    streamChat,
    getSessions,
    getSessionMessages,
    saveAgentResponse,
    getSessionSavedItems,
    deleteSession
} from '../../api/chat';
import { Mic, Send, Bot, User, Check, Sparkles, ArrowRight, Loader2, Save, Package, ChevronDown, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useToast } from '../../context/ToastContext';
import MessageActions from '../../components/MessageActions/MessageActions';
import SessionSwitcher from '../../components/SessionSwitcher/SessionSwitcher';
import ScrollToBottom from '../../components/ScrollToBottom/ScrollToBottom';
import { useNavigate } from 'react-router-dom';

// ─── Response Parser ──────────────────────────────────────────────────────────
// Intelligently extracts structured data from free-text agent responses.

const AGENT_META = {
    meal_planner: {
        key: 'meal_planner_agent',
        label: 'Meal Planner',
        color: 'emerald',
        icon: '🍽️',
        route: '/meals',
    },
    productivity: {
        key: 'productivity_agent',
        label: 'Productivity',
        color: 'purple',
        icon: '📋',
        route: '/productivity',
    },
    study: {
        key: 'study_agent',
        label: 'Study Buddy',
        color: 'blue',
        icon: '📖',
        route: '/study',
    },
    wellness: {
        key: 'wellness_agent',
        label: 'Wellness',
        color: 'teal',
        icon: '💚',
        route: '/wellness',
    },
    shopping: {
        key: 'shopping_agent',
        label: 'Shopping',
        color: 'amber',
        icon: '🛒',
        route: '/shopping',
    },
};

function detectAgentKey(agentName) {
    const name = (agentName || '').toLowerCase().replace(/\s+/g, '_');
    if (name.includes('meal') || name.includes('planner')) return 'meal_planner';
    if (name.includes('productivity') || name.includes('task')) return 'productivity';
    if (name.includes('study') || name.includes('buddy')) return 'study';
    if (name.includes('wellness') || name.includes('health')) return 'wellness';
    if (name.includes('shopping')) return 'shopping';
    // Also handle the raw backend agent key names
    if (name === 'orchestrator' || name === 'agent') return null;
    return null;
}

// Content-based agent detection — used as fallback when metadata is unavailable
function detectAgentFromContent(content) {
    if (!content || content.length < 20) return null;
    const lower = content.toLowerCase();

    // Score-based detection: count domain-specific keywords
    const scores = {
        meal_planner: 0,
        productivity: 0,
        study: 0,
        wellness: 0,
    };

    // Meal signals
    const mealWords = ['recipe', 'ingredient', 'meal', 'cook', 'breakfast', 'lunch', 'dinner', 'snack', 'nutriti', 'calorie', 'protein', 'carb', 'food', 'dish', 'cuisine', 'prep', 'serving'];
    mealWords.forEach(w => { if (lower.includes(w)) scores.meal_planner += 2; });

    // Task/productivity signals
    const taskWords = ['task', 'deadline', 'priority', 'to-do', 'todo', 'schedule', 'organize', 'productivity', 'complete', 'assign', 'project', 'milestone', 'goal', 'action item'];
    taskWords.forEach(w => { if (lower.includes(w)) scores.productivity += 2; });

    // Study signals
    const studyWords = ['study', 'learn', 'subject', 'topic', 'exam', 'quiz', 'flashcard', 'chapter', 'textbook', 'lecture', 'homework', 'assignment', 'course', 'curriculum', 'revision', 'concept'];
    studyWords.forEach(w => { if (lower.includes(w)) scores.study += 2; });

    // Wellness signals
    const wellnessWords = ['exercise', 'workout', 'meditation', 'sleep', 'hydrat', 'water', 'wellness', 'yoga', 'stretch', 'breath', 'mindful', 'mood', 'health', 'relax', 'stress', 'fitness', 'walk', 'run', 'rest'];
    wellnessWords.forEach(w => { if (lower.includes(w)) scores.wellness += 2; });

    // Find the highest scoring agent
    const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    // Only return a result if the top score is significantly above the rest
    if (sorted[0][1] >= 4 && sorted[0][1] > sorted[1][1]) {
        return sorted[0][0];
    }
    return null;
}

// Resolve the best agent name from metadata, agentName, or content
function resolveAgentName(msg) {
    // 1. Check metadata.agent_type (authoritative source from backend)
    const metaAgent = msg.metadata?.agent_type;
    if (metaAgent && metaAgent !== 'orchestrator') {
        return metaAgent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    // 2. Check if agentName already exists and is not generic
    if (msg.agentName && !['orchestrator', 'agent', 'Agent'].includes(msg.agentName?.toLowerCase())) {
        return msg.agentName;
    }

    // 3. Content-based detection as last resort
    const contentKey = detectAgentFromContent(msg.content);
    if (contentKey && AGENT_META[contentKey]) {
        return AGENT_META[contentKey].label + ' Agent';
    }

    return msg.agentName || 'Orchestrator';
}

// ─── Smart Recipe / Meal Parsing ──────────────────────────────────────────────

// Skip AI intro phrases to find the actual recipe/dish name
function extractRecipeName(text) {
    const lines = text.split('\n');
    // Common AI intro patterns we should skip
    const skipPatterns = [
        /^(here'?s?|sure|okay|absolutely|great|of course|i'?d|let me|i recommend)/i,
        /^(for (a|your|tonight|today|this))/i,
        /^(this is|try this|check out|how about)/i,
        /^(you (can|could|might|should))/i,
        /^(a |an |the )(great|healthy|delicious|quick|easy|simple|perfect)/i,
    ];

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // Markdown heading — best source of recipe name
        if (trimmed.startsWith('#')) {
            let name = trimmed.replace(/^#+\s*/, '').replace(/[*_]/g, '').trim();
            // Remove trailing emojis or decoration
            name = name.replace(/\s*[🍽️🥗🍲🍝🍜🍛🥘🥙🌮🌯🍕🍔🥪🥞🍳🥩🍗🥗]+\s*$/g, '').trim();
            // Skip if it's a section heading like "Ingredients" or "Instructions"
            if (/^(ingredients?|instructions?|steps?|directions?|method|preparation|nutritional?|notes?)/i.test(name)) continue;
            if (name.length > 3 && name.length < 150) return name;
        }

        // Bold text line  — likely a recipe name like **Grilled Salmon**
        const boldMatch = trimmed.match(/^\*\*(.+?)\*\*$/);
        if (boldMatch) {
            const name = boldMatch[1].trim();
            if (name.length > 3 && name.length < 150 && !/^(ingredients?|instructions?|steps?|tip)/i.test(name))
                return name;
        }

        // Regular text line — skip AI conversation starters
        if (trimmed.length > 3 && trimmed.length < 150 &&
            !trimmed.startsWith('-') && !trimmed.startsWith('*') && !trimmed.startsWith('•') &&
            !skipPatterns.some(p => p.test(trimmed))) {
            // This is likely the recipe name if it's short enough
            if (trimmed.length < 80) return trimmed.replace(/[.:!]$/, '').trim();
        }
    }
    return null;
}

// Split content into logical sections based on headings/patterns
function splitIntoSections(content) {
    const sections = {};
    let currentSection = '_intro';
    let currentLines = [];

    const sectionPatterns = [
        { key: 'ingredients', pattern: /^(?:#{1,3}\s*)?(?:\*\*)?ingredients?(?:\*\*)?[:\s]*$/i },
        { key: 'ingredients', pattern: /^(?:#{1,3}\s*)?(?:\*\*)?what you'?ll need(?:\*\*)?[:\s]*$/i },
        { key: 'instructions', pattern: /^(?:#{1,3}\s*)?(?:\*\*)?(?:instructions?|directions?|steps?|method|preparation|how to (?:make|prepare|cook))(?:\*\*)?[:\s]*$/i },
        { key: 'nutrition', pattern: /^(?:#{1,3}\s*)?(?:\*\*)?(?:nutritional?\s*(?:info(?:rmation)?|facts?|value)?|macros?|calories)(?:\*\*)?[:\s]*$/i },
        { key: 'tips', pattern: /^(?:#{1,3}\s*)?(?:\*\*)?(?:tips?|notes?|variations?|substitutions?)(?:\*\*)?[:\s]*$/i },
        { key: 'servings', pattern: /^(?:#{1,3}\s*)?(?:\*\*)?(?:servings?|serves?|yield|prep\s*time|cook\s*time)(?:\*\*)?[:\s]*$/i },
    ];

    for (const line of content.split('\n')) {
        const trimmed = line.trim();
        let matched = false;
        for (const { key, pattern } of sectionPatterns) {
            if (pattern.test(trimmed)) {
                sections[currentSection] = currentLines.join('\n');
                currentSection = key;
                currentLines = [];
                matched = true;
                break;
            }
        }
        if (!matched) {
            currentLines.push(line);
        }
    }
    sections[currentSection] = currentLines.join('\n');
    return sections;
}

// Extract ingredients from a section of text
function extractIngredients(content) {
    const ingredients = [];
    const lines = content.split('\n');
    for (const line of lines) {
        const trimmed = line.trim();
        // Bullet/numbered list items
        const match = trimmed.match(/^(?:[-*•]|\d+[.)]\s)\s*(.*)/);
        if (match && match[1].trim().length > 1) {
            ingredients.push(match[1].trim());
        }
    }
    return ingredients;
}

// Extract nutritional data
function extractNutrition(content) {
    const nutrition = {};
    const lower = content.toLowerCase();

    const calMatch = lower.match(/(\d+)\s*(?:kcal|calories?|cal\b)/i);
    if (calMatch) nutrition.calories = parseInt(calMatch[1]);

    const protMatch = lower.match(/(\d+)\s*g?\s*(?:of\s*)?protein/i);
    if (protMatch) nutrition.protein = `${protMatch[1]}g`;

    const carbMatch = lower.match(/(\d+)\s*g?\s*(?:of\s*)?carb(?:ohydrate)?s?/i);
    if (carbMatch) nutrition.carbs = `${carbMatch[1]}g`;

    const fatMatch = lower.match(/(\d+)\s*g?\s*(?:of\s*)?(?:total\s*)?fat/i);
    if (fatMatch) nutrition.fat = `${fatMatch[1]}g`;

    const fiberMatch = lower.match(/(\d+)\s*g?\s*(?:of\s*)?fiber/i);
    if (fiberMatch) nutrition.fiber = `${fiberMatch[1]}g`;

    return Object.keys(nutrition).length > 0 ? nutrition : null;
}

// Extract prep/cook time
function extractTimes(content) {
    const times = {};
    const prepMatch = content.match(/prep(?:\s*time)?[:\s]*(?:about\s*)?(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);
    if (prepMatch) times.prep = `${prepMatch[1]} min`;

    const cookMatch = content.match(/cook(?:ing)?(?:\s*time)?[:\s]*(?:about\s*)?(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);
    if (cookMatch) times.cook = `${cookMatch[1]} min`;

    const totalMatch = content.match(/total(?:\s*time)?[:\s]*(?:about\s*)?(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);
    if (totalMatch) times.total = `${totalMatch[1]} min`;

    return Object.keys(times).length > 0 ? times : null;
}

function parseMealData(content) {
    const recipeName = extractRecipeName(content);
    const sections = splitIntoSections(content);

    // Detect meal_type
    const lower = content.toLowerCase();
    let meal_type = 'dinner';
    if (lower.includes('breakfast')) meal_type = 'breakfast';
    else if (lower.includes('lunch')) meal_type = 'lunch';
    else if (lower.includes('snack')) meal_type = 'snack';

    // Extract ingredients — prefer dedicated section, fallback to full content scan
    let ingredients = [];
    if (sections.ingredients) {
        ingredients = extractIngredients(sections.ingredients);
    }
    if (ingredients.length === 0) {
        // Try to find ingredients in the full content
        const ingBlockMatch = content.match(/(?:ingredients?|what you'?ll need)[:\s]*\n((?:[\t ]*[-*•]\s*.+\n?)+)/i);
        if (ingBlockMatch) {
            ingredients = extractIngredients(ingBlockMatch[1]);
        }
    }

    // Extract instructions — prefer dedicated section, else use everything except ingredients
    let instructions = '';
    if (sections.instructions) {
        instructions = sections.instructions.trim();
    } else {
        // Build instructions from non-ingredient, non-intro content
        const nonIngredientParts = [];
        for (const [key, val] of Object.entries(sections)) {
            if (key !== 'ingredients' && key !== '_intro' && key !== 'nutrition' && key !== 'tips' && key !== 'servings') {
                nonIngredientParts.push(val);
            }
        }
        instructions = nonIngredientParts.join('\n').trim() || content;
    }

    // Nutritional info
    const nutritional_info = extractNutrition(sections.nutrition || content);

    // Times
    const times = extractTimes(content);

    // Preferences/metadata
    const preferences = {};
    if (times) preferences.times = times;
    if (sections.tips) preferences.tips = sections.tips.trim().slice(0, 500);

    return {
        date: new Date().toISOString().split('T')[0],
        meal_type,
        meal_name: recipeName || 'AI-Generated Recipe',
        instructions: instructions,
        ingredients: ingredients.length > 0 ? ingredients : null,
        nutritional_info,
        preferences: Object.keys(preferences).length > 0 ? preferences : null,
    };
}

function extractTitle(text) {
    const lines = text.split('\n');
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('#')) return trimmed.replace(/^#+\s*/, '').slice(0, 200);
        if (trimmed.length > 0 && trimmed.length < 200 && !trimmed.startsWith('-') && !trimmed.startsWith('*'))
            return trimmed;
    }
    return null;
}

function parseTaskData(content) {
    const title = extractTitle(content);
    // Try to identify multiple tasks
    const lines = content.split('\n');
    const tasks = [];
    for (const line of lines) {
        const trimmed = line.trim();
        // Lines starting with numbers or checkboxes are likely task items
        const match = trimmed.match(/^(?:\d+[.)]\s*|[-*•]\s*(?:\[[ x]\]\s*)?)(.*)/i);
        if (match && match[1].trim().length > 3 && match[1].trim().length < 200) {
            tasks.push(match[1].trim());
        }
    }

    return {
        title: title || 'AI-Generated Task',
        description: content,
        priority: content.toLowerCase().includes('urgent') ? 'urgent'
            : content.toLowerCase().includes('high priority') ? 'high'
                : 'medium',
        status: 'todo',
        // We'll also return extracted sub-tasks for potential multi-save
        _subtasks: tasks.length > 1 ? tasks : null,
    };
}

function parseStudyData(content) {
    const title = extractTitle(content);
    // Try to detect subject/topic
    let subject = title || 'Study Session';
    let topic = null;
    const topicMatch = content.match(/(?:topic|subject|focus)[:\s]+([^\n]+)/i);
    if (topicMatch) {
        subject = topicMatch[1].trim().slice(0, 200);
    }

    // Duration heuristic
    let duration = 60;
    const durMatch = content.match(/(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);
    if (durMatch) {
        duration = parseInt(durMatch[1]);
        if (content.match(/hours?/i) && duration < 10) duration *= 60;
    }

    return {
        subject,
        topic,
        duration,
        notes: content,
    };
}

function parseWellnessData(content) {
    const lower = content.toLowerCase();
    let activity_type = 'exercise';
    if (lower.includes('meditat')) activity_type = 'meditation';
    else if (lower.includes('sleep')) activity_type = 'sleep';
    else if (lower.includes('hydrat') || lower.includes('water')) activity_type = 'hydration';
    else if (lower.includes('mood') || lower.includes('mental')) activity_type = 'mood';

    let duration = null;
    const durMatch = content.match(/(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);
    if (durMatch) {
        duration = parseInt(durMatch[1]);
        if (content.match(/hours?/i) && duration < 10) duration *= 60;
    }

    return {
        activity_type,
        duration,
        notes: content,
        recorded_at: new Date().toISOString(),
    };
}

function buildSavePayload(agentKey, content) {
    switch (agentKey) {
        case 'meal_planner': return { agent_type: 'meal_planner_agent', data: parseMealData(content) };
        case 'productivity': return { agent_type: 'productivity_agent', data: parseTaskData(content) };
        case 'study': return { agent_type: 'study_agent', data: parseStudyData(content) };
        case 'wellness': return { agent_type: 'wellness_agent', data: parseWellnessData(content) };
        default: return { agent_type: 'productivity_agent', data: parseTaskData(content) };
    }
}

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
    const [savedItemsMap, setSavedItemsMap] = useState({}); // msgIndex -> saved info
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const messagesContainerRef = useRef(null);
    const historyLoadedRef = useRef(false);
    const toast = useToast();
    const navigate = useNavigate();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

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
                const sessionsResponse = await getSessions();
                const loadedSessions = sessionsResponse.data;
                setSessions(loadedSessions);

                if (loadedSessions && loadedSessions.length > 0) {
                    const lastSession = loadedSessions[0];
                    setSessionId(lastSession.session_id);

                    const messagesResponse = await getSessionMessages(lastSession.session_id);
                    const loadedMessages = messagesResponse.data.map(msg => ({
                        role: msg.role,
                        content: msg.content,
                        metadata: msg.metadata || null,
                        timestamp: msg.created_at || new Date().toISOString(),
                        agentName: msg.role === 'agent'
                            ? resolveAgentName(msg)
                            : null
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
                agentName: msg.role === 'agent'
                    ? resolveAgentName(msg)
                    : null
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
                if (!sessionId && data.session_id) {
                    setSessionId(data.session_id);
                }
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    lastMsg.agentName = data.agent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    lastMsg._rawAgent = data.agent; // Keep raw agent name for routing
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

    const handleRegenerateResponse = async (index) => {
        const userMessageIndex = index - 1;
        if (userMessageIndex >= 0 && messages[userMessageIndex].role === 'user') {
            setMessages(prev => prev.filter((_, i) => i !== index));
            const userContent = messages[userMessageIndex].content;
            setInput(userContent);
        }
    };

    const toggleListening = () => {
        if (!isListening) {
            // Real Speech-to-Text using Web Speech API
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    setInput(prev => prev + transcript);
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

    // ─── DraftCard: Smart save-to-agent card ─────────────────────────────
    const DraftCard = ({ content, agentName, rawAgent, timestamp, onCopy, onDelete, msgIndex }) => {
        const [saving, setSaving] = useState(false);
        const [saved, setSaved] = useState(savedItemsMap[msgIndex] || false);
        const [showDetails, setShowDetails] = useState(false);

        const agentKey = detectAgentKey(agentName);
        const meta = agentKey ? AGENT_META[agentKey] : null;
        const isActionable = content && (content.includes('-') || content.includes('\n') || content.length > 80);

        // Build preview of what will be saved
        const previewPayload = agentKey ? buildSavePayload(agentKey, content) : null;

        const handleSave = async () => {
            setSaving(true);
            try {
                if (!agentKey) {
                    // Fallback: save as task
                    const payload = buildSavePayload(null, content);
                    await saveAgentResponse({
                        agent_type: payload.agent_type,
                        session_id: sessionId,
                        data: payload.data,
                    });
                } else {
                    const payload = buildSavePayload(agentKey, content);
                    await saveAgentResponse({
                        agent_type: payload.agent_type,
                        session_id: sessionId,
                        data: payload.data,
                    });
                }

                setSaved(true);
                setSavedItemsMap(prev => ({ ...prev, [msgIndex]: true }));
                const targetLabel = meta?.label || 'Productivity';
                toast.success(`✅ Saved to ${targetLabel}!`);
            } catch (error) {
                console.error('Failed to save:', error);
                const errMsg = error?.response?.data?.errors
                    ? Object.values(error.response.data.errors).flat().join(', ')
                    : error?.response?.data?.error || 'Failed to save. Please try again.';
                toast.error(errMsg);
            } finally {
                setSaving(false);
            }
        };

        const accentMap = {
            emerald: {
                bg: 'from-emerald-500/20 to-emerald-600/10',
                border: 'border-emerald-500/20',
                btnBg: 'bg-emerald-500/20 hover:bg-emerald-500/30 border-emerald-500/30',
                btnSaved: 'bg-emerald-500/30 border-emerald-500/50 text-emerald-300',
                text: 'text-emerald-400',
            },
            purple: {
                bg: 'from-purple-500/20 to-purple-600/10',
                border: 'border-purple-500/20',
                btnBg: 'bg-purple-500/20 hover:bg-purple-500/30 border-purple-500/30',
                btnSaved: 'bg-purple-500/30 border-purple-500/50 text-purple-300',
                text: 'text-purple-400',
            },
            blue: {
                bg: 'from-blue-500/20 to-blue-600/10',
                border: 'border-blue-500/20',
                btnBg: 'bg-blue-500/20 hover:bg-blue-500/30 border-blue-500/30',
                btnSaved: 'bg-blue-500/30 border-blue-500/50 text-blue-300',
                text: 'text-blue-400',
            },
            teal: {
                bg: 'from-teal-500/20 to-teal-600/10',
                border: 'border-teal-500/20',
                btnBg: 'bg-teal-500/20 hover:bg-teal-500/30 border-teal-500/30',
                btnSaved: 'bg-teal-500/30 border-teal-500/50 text-teal-300',
                text: 'text-teal-400',
            },
            amber: {
                bg: 'from-amber-500/20 to-amber-600/10',
                border: 'border-amber-500/20',
                btnBg: 'bg-amber-500/20 hover:bg-amber-500/30 border-amber-500/30',
                btnSaved: 'bg-amber-500/30 border-amber-500/50 text-amber-300',
                text: 'text-amber-400',
            },
        };

        const accent = meta ? accentMap[meta.color] : accentMap.purple;

        return (
            <div className={`bg-gradient-to-br ${accent.bg} ${accent.border} border rounded-2xl p-5 mt-2 group transition-all duration-300`}>
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white/50">
                        {meta ? <span>{meta.icon}</span> : <Sparkles size={12} className="text-yellow-400" />}
                        <span>{agentName || 'Agent'}</span>
                        {meta && (
                            <button
                                onClick={() => navigate(meta.route)}
                                className="ml-2 flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-white/10 hover:bg-white/20 text-white/40 hover:text-white/70 transition-all"
                                title={`Go to ${meta.label}`}
                            >
                                <ExternalLink size={9} />
                                View
                            </button>
                        )}
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

                {/* Content */}
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

                {/* Save Data Preview (collapsible) */}
                {isActionable && previewPayload && !saved && (
                    <div className="mb-3">
                        <button
                            onClick={() => setShowDetails(!showDetails)}
                            className="flex items-center gap-1 text-xs text-white/40 hover:text-white/60 transition-colors"
                        >
                            <ChevronDown size={12} className={`transition-transform ${showDetails ? 'rotate-180' : ''}`} />
                            Preview what will be saved
                        </button>
                        <AnimatePresence>
                            {showDetails && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden"
                                >
                                    <div className="mt-2 p-3 bg-black/20 rounded-lg border border-white/5 text-xs text-white/50 font-mono space-y-1">
                                        <div><span className="text-white/30">Target:</span> <span className={accent.text}>{meta?.label || 'Tasks'}</span></div>
                                        {Object.entries(previewPayload.data).filter(([k]) => !k.startsWith('_')).slice(0, 5).map(([key, value]) => (
                                            <div key={key} className="truncate">
                                                <span className="text-white/30">{key}:</span>{' '}
                                                <span className="text-white/60">{typeof value === 'object' ? JSON.stringify(value)?.slice(0, 80) : String(value).slice(0, 80)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}

                {/* Action Buttons */}
                {isActionable && (
                    <div className="flex gap-2">
                        <button
                            onClick={handleSave}
                            disabled={saving || saved}
                            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all text-sm flex-1 justify-center font-medium border ${saved
                                ? accent.btnSaved
                                : `${accent.btnBg} text-white`
                                } disabled:cursor-not-allowed`}
                        >
                            {saving ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Saving to {meta?.label || 'Tasks'}...
                                </>
                            ) : saved ? (
                                <>
                                    <Check size={16} />
                                    Saved to {meta?.label || 'Tasks'}
                                </>
                            ) : (
                                <>
                                    <Save size={16} />
                                    Save to {meta?.label || 'Tasks'}
                                </>
                            )}
                        </button>
                        {saved && meta && (
                            <motion.button
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                onClick={() => navigate(meta.route)}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-sm border border-white/10 transition-all"
                            >
                                <ExternalLink size={14} />
                                View
                            </motion.button>
                        )}
                    </div>
                )}
            </div>
        );
    };

    // ─── Suggested Prompts ────────────────────────────────────────────────
    const suggestedPrompts = [
        { label: '🍽️ Plan dinner', text: 'Plan a healthy dinner for tonight with easy ingredients' },
        { label: '📋 Organize tasks', text: 'Help me organize my tasks for this week' },
        { label: '📖 Study plan', text: 'Create a study plan for learning Data Structures' },
        { label: '💚 Wellness check', text: 'Suggest a 20-minute morning wellness routine' },
    ];

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
                <p className="text-white/60">Your AI command center — responses are auto-routed to the right agent.</p>
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
                    <div className="h-full flex flex-col items-center justify-center">
                        <div className="relative mb-8">
                            <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/30 to-purple-500/30 rounded-full blur-2xl scale-150" />
                            <Bot size={64} className="text-white/30 relative" />
                        </div>
                        <p className="text-white/40 text-lg mb-8">How can I help you today?</p>
                        {/* Suggested Prompts */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
                            {suggestedPrompts.map((prompt, i) => (
                                <motion.button
                                    key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    onClick={() => { setInput(prompt.text); inputRef.current?.focus(); }}
                                    className="text-left p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all text-sm group"
                                >
                                    <span className="text-white/70 group-hover:text-white transition-colors">
                                        {prompt.label}
                                    </span>
                                    <p className="text-white/30 text-xs mt-1 truncate">{prompt.text}</p>
                                </motion.button>
                            ))}
                        </div>
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
                                                rawAgent={msg._rawAgent}
                                                timestamp={msg.timestamp}
                                                msgIndex={idx}
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
