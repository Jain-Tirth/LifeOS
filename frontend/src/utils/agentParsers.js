/**
 * Agent metadata and response parsing utilities.
 * Extracts structured data from free-text LLM responses so they can be saved
 * to the correct database models (MealPlan, Task, StudySession, WellnessActivity).
 */

// ─── Agent Metadata ───────────────────────────────────────────────────────────

export const AGENT_META = {
    meal_planner: {
        key: 'meal_planner_agent',
        label: 'Meal Planner',
        color: 'emerald',
        route: '/meals',
        icon: '🍽️',
    },
    productivity: {
        key: 'productivity_agent',
        label: 'Productivity',
        color: 'purple',
        route: '/productivity',
        icon: '📋',
    },
    study: {
        key: 'study_agent',
        label: 'Study Buddy',
        color: 'blue',
        route: '/study',
        icon: '📚',
    },
    wellness: {
        key: 'wellness_agent',
        label: 'Wellness',
        color: 'teal',
        route: '/wellness',
        icon: '🧘',
    },
    habit_coach: {
        key: 'habit_coach_agent',
        label: 'Habit Coach',
        color: 'amber',
        route: '/habits',
        icon: '⚡',
    },
};

// ─── Agent Detection ──────────────────────────────────────────────────────────

export function detectAgentKey(agentName) {
    const name = (agentName || '').toLowerCase().replace(/\s+/g, '_');
    if (name.includes('habit') || name.includes('coach')) return 'habit_coach';
    if (name.includes('meal') || name.includes('planner')) return 'meal_planner';
    if (name.includes('productivity') || name.includes('task')) return 'productivity';
    if (name.includes('study') || name.includes('buddy')) return 'study';
    if (name.includes('wellness') || name.includes('health')) return 'wellness';
    if (name === 'orchestrator' || name === 'agent') return null;
    return null;
}

export function detectAgentFromContent(content) {
    if (!content || content.length < 20) return null;
    const lower = content.toLowerCase();

    const scores = { meal_planner: 0, productivity: 0, study: 0, wellness: 0 };

    const mealWords = ['recipe', 'ingredient', 'meal', 'cook', 'breakfast', 'lunch', 'dinner', 'snack', 'nutriti', 'calorie', 'protein', 'carb', 'food', 'dish', 'cuisine', 'prep', 'serving'];
    mealWords.forEach(w => { if (lower.includes(w)) scores.meal_planner += 2; });

    const taskWords = ['task', 'deadline', 'priority', 'to-do', 'todo', 'schedule', 'organize', 'productivity', 'complete', 'assign', 'project', 'milestone', 'goal', 'action item'];
    taskWords.forEach(w => { if (lower.includes(w)) scores.productivity += 2; });

    const studyWords = ['study', 'learn', 'subject', 'topic', 'exam', 'quiz', 'flashcard', 'chapter', 'textbook', 'lecture', 'homework', 'assignment', 'course', 'curriculum', 'revision', 'concept'];
    studyWords.forEach(w => { if (lower.includes(w)) scores.study += 2; });

    const wellnessWords = ['exercise', 'workout', 'meditation', 'sleep', 'hydrat', 'water', 'wellness', 'yoga', 'stretch', 'breath', 'mindful', 'mood', 'health', 'relax', 'stress', 'fitness', 'walk', 'run', 'rest'];
    wellnessWords.forEach(w => { if (lower.includes(w)) scores.wellness += 2; });

    const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    if (sorted[0][1] >= 4 && sorted[0][1] > sorted[1][1]) return sorted[0][0];
    return null;
}

export function resolveAgentName(msg) {
    const metaAgent = msg.metadata?.agent_type;
    if (metaAgent && metaAgent !== 'orchestrator') {
        return metaAgent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    if (msg.agentName && !['orchestrator', 'agent', 'Agent'].includes(msg.agentName?.toLowerCase())) {
        return msg.agentName;
    }
    const contentKey = detectAgentFromContent(msg.content);
    if (contentKey && AGENT_META[contentKey]) return AGENT_META[contentKey].label + ' Agent';
    return msg.agentName || 'Orchestrator';
}

// ─── Content Parsing Helpers ──────────────────────────────────────────────────

function stripChatter(content) {
    const parts = content.split('---');
    if (parts.length > 1) return parts.slice(1).join('---').trim();
    return content;
}

function extractRecipeName(text) {
    const lines = text.split('\n');
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
        if (trimmed.startsWith('#')) {
            let name = trimmed.replace(/^#+\s*/, '').replace(/[*_]/g, '').trim();
            name = name.replace(/\s*[🍽️🥗🍲🍝🍜🍛🥘🥙🌮🌯🍕🍔🥪🥞🍳🥩🍗🥗]+\s*$/g, '').trim();
            if (/^(ingredients?|instructions?|steps?|directions?|method|preparation|nutritional?|notes?)/i.test(name)) continue;
            if (name.length > 3 && name.length < 150) return name;
        }
        const boldMatch = trimmed.match(/^\*\*(.+?)\*\*$/);
        if (boldMatch) {
            const name = boldMatch[1].trim();
            if (name.length > 3 && name.length < 150 && !/^(ingredients?|instructions?|steps?|tip)/i.test(name)) return name;
        }
        if (trimmed.length > 3 && trimmed.length < 150 &&
            !trimmed.startsWith('-') && !trimmed.startsWith('*') && !trimmed.startsWith('•') &&
            !skipPatterns.some(p => p.test(trimmed))) {
            if (trimmed.length < 80) return trimmed.replace(/[.:!]$/, '').trim();
        }
    }
    return null;
}

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
        if (!matched) currentLines.push(line);
    }
    sections[currentSection] = currentLines.join('\n');
    return sections;
}

function extractIngredients(content) {
    const ingredients = [];
    for (const line of content.split('\n')) {
        const match = line.trim().match(/^(?:[-*•]|\d+[.)]\s)\s*(.*)/);
        if (match && match[1].trim().length > 1) ingredients.push(match[1].trim());
    }
    return ingredients;
}

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

function extractTitle(text) {
    for (const line of text.split('\n')) {
        const trimmed = line.trim();
        if (trimmed.startsWith('#')) return trimmed.replace(/^#+\s*/, '').slice(0, 200);
        if (trimmed.length > 0 && trimmed.length < 200 && !trimmed.startsWith('-') && !trimmed.startsWith('*'))
            return trimmed;
    }
    return null;
}

// ─── Agent-Specific Parsers ───────────────────────────────────────────────────

export function parseMealData(content) {
    const cleanContent = stripChatter(content);
    const recipeName = extractRecipeName(cleanContent);
    const sections = splitIntoSections(cleanContent);

    const lower = cleanContent.toLowerCase();
    let meal_type = 'dinner';
    if (lower.includes('breakfast')) meal_type = 'breakfast';
    else if (lower.includes('lunch')) meal_type = 'lunch';
    else if (lower.includes('snack')) meal_type = 'snack';

    let ingredients = [];
    if (sections.ingredients) ingredients = extractIngredients(sections.ingredients);
    if (ingredients.length === 0) {
        const ingBlockMatch = cleanContent.match(/(?:ingredients?|what you'?ll need)[:\s]*\n((?:[\t ]*[-*•]\s*.+\n?)+)/i);
        if (ingBlockMatch) ingredients = extractIngredients(ingBlockMatch[1]);
    }

    let instructions = '';
    if (sections.instructions) {
        instructions = sections.instructions.trim();
    } else {
        const nonIngredientParts = [];
        for (const [key, val] of Object.entries(sections)) {
            if (!['ingredients', '_intro', 'nutrition', 'tips', 'servings'].includes(key)) nonIngredientParts.push(val);
        }
        instructions = nonIngredientParts.join('\n').trim() || cleanContent;
    }

    const nutritional_info = extractNutrition(sections.nutrition || cleanContent);
    const times = extractTimes(cleanContent);
    const preferences = {};
    if (times) preferences.times = times;
    if (sections.tips) preferences.tips = sections.tips.trim().slice(0, 500);

    return {
        date: new Date().toISOString().split('T')[0],
        meal_type,
        meal_name: recipeName || 'AI-Generated Recipe',
        instructions,
        ingredients: ingredients.length > 0 ? ingredients : null,
        nutritional_info,
        preferences: Object.keys(preferences).length > 0 ? preferences : null,
    };
}

export function parseTaskData(content) {
    const cleanContent = stripChatter(content);
    const title = extractTitle(cleanContent);
    const tasks = [];
    for (const line of cleanContent.split('\n')) {
        const match = line.trim().match(/^(?:\d+[.)]\s*|[-*•]\s*(?:\[[ x]\]\s*)?)(.*)/i);
        if (match && match[1].trim().length > 3 && match[1].trim().length < 200) tasks.push(match[1].trim());
    }
    return {
        title: title || 'AI-Generated Task',
        description: cleanContent,
        priority: cleanContent.toLowerCase().includes('urgent') ? 'urgent'
            : cleanContent.toLowerCase().includes('high priority') ? 'high' : 'medium',
        status: 'todo',
        _subtasks: tasks.length > 1 ? tasks : null,
    };
}

export function parseStudyData(content) {
    const cleanContent = stripChatter(content);
    const title = extractTitle(cleanContent);
    let subject = title || 'Study Session';
    const topicMatch = cleanContent.match(/(?:topic|subject|focus)[:\s]+([^\n]+)/i);
    if (topicMatch) subject = topicMatch[1].trim().slice(0, 200);

    let duration = 60;
    const durMatch = cleanContent.match(/(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);
    if (durMatch) {
        duration = parseInt(durMatch[1]);
        if (cleanContent.match(/hours?/i) && duration < 10) duration *= 60;
    }

    return { subject, topic: null, duration, notes: cleanContent };
}

export function parseWellnessData(content) {
    const cleanContent = stripChatter(content);
    const lower = cleanContent.toLowerCase();
    let activity_type = 'exercise';
    if (lower.includes('meditat')) activity_type = 'meditation';
    else if (lower.includes('sleep')) activity_type = 'sleep';
    else if (lower.includes('hydrat') || lower.includes('water')) activity_type = 'hydration';
    else if (lower.includes('mood') || lower.includes('mental')) activity_type = 'mood';

    let duration = null;
    const durMatch = cleanContent.match(/(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);
    if (durMatch) {
        duration = parseInt(durMatch[1]);
        if (cleanContent.match(/hours?/i) && duration < 10) duration *= 60;
    }

    return { activity_type, duration, notes: cleanContent, recorded_at: new Date().toISOString() };
}

export function buildSavePayload(agentKey, content) {
    switch (agentKey) {
        case 'meal_planner': return { agent_type: 'meal_planner_agent', data: parseMealData(content) };
        case 'productivity': return { agent_type: 'productivity_agent', data: parseTaskData(content) };
        case 'study': return { agent_type: 'study_agent', data: parseStudyData(content) };
        case 'wellness': return { agent_type: 'wellness_agent', data: parseWellnessData(content) };
        default: return { agent_type: 'productivity_agent', data: parseTaskData(content) };
    }
}
