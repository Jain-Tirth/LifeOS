/**
 * AgentOutputRenderer — Sprint 3, Mission 2: Structured Agent Output Rendering
 *
 * Schema-driven rendering for agent-specific structured data.
 * Instead of letting DraftCard regex-parse everything into generic markdown,
 * we detect the agent type and render purpose-built UI blocks.
 *
 * Supported schemas:
 *   - MealPlanRenderer      (meal_planner_agent)
 *   - TaskListRenderer      (productivity_agent)
 *   - StudyPlanRenderer     (study_agent)
 *   - WellnessRenderer      (wellness_agent)
 *   - HabitRenderer         (habit_coach_agent)
 *   - GenericMarkdownRenderer (fallback for orchestrator / unknown agents)
 */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { detectAgentKey } from '../../utils/agentParsers';

// ─── Shared Markdown components ───────────────────────────────────────────────
export const MD = {
    h1: ({ children }) => <h1 className="text-xl font-bold text-white mb-2 mt-3">{children}</h1>,
    h2: ({ children }) => <h2 className="text-lg font-bold text-white mb-1.5 mt-2">{children}</h2>,
    h3: ({ children }) => <h3 className="text-base font-semibold text-white mb-1 mt-2">{children}</h3>,
    p: ({ children }) => <p className="text-white/80 mb-2 leading-relaxed">{children}</p>,
    ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5 text-white/80">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-0.5 text-white/80">{children}</ol>,
    li: ({ children }) => <li className="text-white/80 ml-2">{children}</li>,
    code: ({ inline, children }) =>
        inline
            ? <code className="bg-white/10 px-1.5 py-0.5 rounded text-sm font-mono text-yellow-300">{children}</code>
            : <code className="block bg-white/10 p-3 rounded-lg text-sm font-mono text-yellow-300 my-2 overflow-x-auto whitespace-pre-wrap">{children}</code>,
    strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
    em: ({ children }) => <em className="italic text-white/90">{children}</em>,
    blockquote: ({ children }) => <blockquote className="border-l-4 border-purple-400 pl-4 italic text-white/70 my-2">{children}</blockquote>,
    table: ({ children }) => (
        <div className="overflow-x-auto my-3">
            <table className="min-w-full text-sm border-collapse">{children}</table>
        </div>
    ),
    thead: ({ children }) => <thead className="border-b border-white/10">{children}</thead>,
    tbody: ({ children }) => <tbody>{children}</tbody>,
    tr: ({ children }) => <tr className="border-b border-white/5">{children}</tr>,
    th: ({ children }) => <th className="py-2 px-3 text-left text-white/50 font-semibold text-xs uppercase">{children}</th>,
    td: ({ children }) => <td className="py-2 px-3 text-white/80">{children}</td>,
};

// ─── Utility: extract sections from markdown ──────────────────────────────────
function extractSections(text) {
    const sections = {};
    let current = '_intro';
    let buf = [];
    for (const line of text.split('\n')) {
        const headerMatch = line.match(/^#{1,3}\s+(.+)/);
        if (headerMatch) {
            sections[current] = buf.join('\n').trim();
            current = headerMatch[1].toLowerCase().replace(/\s+/g, '_').replace(/[^\w]/g, '');
            buf = [];
        } else {
            buf.push(line);
        }
    }
    sections[current] = buf.join('\n').trim();
    return sections;
}

// ─── Schema block components ──────────────────────────────────────────────────

function InfoBadge({ label, value, color = 'white' }) {
    return (
        <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-wider text-white/30 font-semibold">{label}</span>
            <span className={`text-sm font-medium text-${color}-300`}>{value}</span>
        </div>
    );
}

function SectionCard({ title, children, accent = 'white' }) {
    return (
        <div className="mb-3">
            <div className={`text-xs font-bold uppercase tracking-wider text-${accent}-400/70 mb-1.5`}>{title}</div>
            {children}
        </div>
    );
}

// ─── Meal Planner Renderer ────────────────────────────────────────────────────
/**
 * Renders meal content with structured ingredient list + instructions + macros.
 * Falls back to markdown if content has no structured markers.
 */
export function MealPlanRenderer({ content }) {
    const sections = extractSections(content);
    const hasIngredients = content.toLowerCase().includes('ingredient');
    const hasInstructions =
        content.toLowerCase().includes('instruction') ||
        content.toLowerCase().includes('step') ||
        content.toLowerCase().includes('direction');

    // If content is structured enough, render with UI blocks
    if (hasIngredients || hasInstructions) {
        // Extract bullet items from a section block
        const extractBullets = (text) =>
            (text || '').split('\n')
                .map(l => l.trim().replace(/^[-*•\d]+[.)]\s*/, ''))
                .filter(l => l.length > 1);

        const ingredients = extractBullets(sections['ingredients'] || sections['what_youll_need'] || '');
        const instructionText = sections['instructions'] || sections['steps'] || sections['directions'] || sections['method'] || '';
        const nutritionText = sections['nutritional_info'] || sections['nutrition'] || sections['macros'] || '';
        const intro = sections['_intro'] || '';

        return (
            <div className="space-y-3">
                {/* Intro / name */}
                {intro && (
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>{intro}</ReactMarkdown>
                    </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {/* Ingredients */}
                    {ingredients.length > 0 && (
                        <SectionCard title="🧂 Ingredients" accent="emerald">
                            <ul className="space-y-1">
                                {ingredients.map((ing, i) => (
                                    <li key={i} className="flex items-start gap-1.5 text-sm text-white/70">
                                        <span className="text-emerald-400/60 mt-0.5">•</span>
                                        <span>{ing}</span>
                                    </li>
                                ))}
                            </ul>
                        </SectionCard>
                    )}

                    {/* Instructions */}
                    {instructionText && (
                        <SectionCard title="👨‍🍳 Instructions" accent="blue">
                            <div className="prose prose-invert prose-sm max-w-none">
                                <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>
                                    {instructionText}
                                </ReactMarkdown>
                            </div>
                        </SectionCard>
                    )}
                </div>

                {/* Nutrition */}
                {nutritionText && (
                    <SectionCard title="📊 Nutrition" accent="amber">
                        <div className="prose prose-invert prose-sm max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>{nutritionText}</ReactMarkdown>
                        </div>
                    </SectionCard>
                )}
            </div>
        );
    }

    return <GenericMarkdownRenderer content={content} />;
}

// ─── Productivity / Task Renderer ─────────────────────────────────────────────
function priorityBadge(text) {
    const lower = text.toLowerCase();
    if (lower.includes('urgent')) return { label: 'Urgent', cls: 'bg-red-500/20 text-red-300 border-red-500/30' };
    if (lower.includes('high')) return { label: 'High', cls: 'bg-amber-500/20 text-amber-300 border-amber-500/30' };
    if (lower.includes('low')) return { label: 'Low', cls: 'bg-blue-500/20 text-blue-300 border-blue-500/30' };
    return { label: 'Medium', cls: 'bg-purple-500/20 text-purple-300 border-purple-500/30' };
}

export function TaskListRenderer({ content }) {
    // Extract numbered or bulleted list items as tasks
    const taskLines = content.split('\n').filter(l =>
        /^(\d+[.)]\s|[-*•]\s|\[[ x]\]\s)/.test(l.trim())
    );

    const hasTaskList = taskLines.length >= 2;
    const priority = priorityBadge(content);
    const deadlineMatch = content.match(/(?:due|deadline|by)[:\s]+([^\n,]+)/i);

    if (hasTaskList) {
        const cleanTask = (l) =>
            l.trim()
                .replace(/^\d+[.)]\s*/, '')
                .replace(/^[-*•]\s*/, '')
                .replace(/^\[[ x]\]\s*/, '')
                .trim();

        return (
            <div className="space-y-3">
                {/* Priority + deadline badges */}
                <div className="flex flex-wrap gap-2">
                    <span className={`text-[11px] px-2 py-0.5 rounded-full border font-medium ${priority.cls}`}>
                        {priority.label} Priority
                    </span>
                    {deadlineMatch && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full border bg-white/5 border-white/10 text-white/50">
                            📅 {deadlineMatch[1].trim().slice(0, 40)}
                        </span>
                    )}
                </div>

                {/* Task items */}
                <div className="space-y-1.5">
                    {taskLines.map((line, i) => (
                        <div
                            key={i}
                            className="flex items-start gap-2.5 p-2.5 bg-white/5 rounded-lg border border-white/5 hover:border-white/10 transition-colors group"
                        >
                            <div className="w-5 h-5 rounded border border-white/20 group-hover:border-purple-400/40 flex-shrink-0 mt-0.5 transition-colors" />
                            <span className="text-sm text-white/80 leading-snug">{cleanTask(line)}</span>
                        </div>
                    ))}
                </div>

                {/* Any non-list context */}
                {(() => {
                    const nonListText = content.split('\n')
                        .filter(l => !/^(\d+[.)]\s|[-*•]\s|\[[ x]\]\s)/.test(l.trim()) && l.trim())
                        .join('\n').trim();
                    return nonListText
                        ? (
                            <div className="prose prose-invert prose-sm max-w-none pt-1 border-t border-white/5">
                                <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>{nonListText}</ReactMarkdown>
                            </div>
                        )
                        : null;
                })()}
            </div>
        );
    }

    return <GenericMarkdownRenderer content={content} />;
}

// ─── Study Plan Renderer ──────────────────────────────────────────────────────
export function StudyPlanRenderer({ content }) {
    const durMatch = content.match(/(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);
    const duration = durMatch ? durMatch[0] : null;
    const sections = extractSections(content);

    return (
        <div className="space-y-3">
            {/* Duration badge */}
            {duration && (
                <div className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300">
                    ⏱️ {duration}
                </div>
            )}

            {/* Render all sections */}
            {Object.entries(sections).map(([key, text]) => {
                if (!text.trim()) return null;
                const title = key === '_intro' ? null : key.replace(/_/g, ' ');
                return (
                    <div key={key}>
                        {title && (
                            <div className="text-xs font-bold uppercase tracking-wider text-blue-400/70 mb-1.5">
                                📖 {title}
                            </div>
                        )}
                        <div className="prose prose-invert prose-sm max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>{text}</ReactMarkdown>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

// ─── Wellness Renderer ────────────────────────────────────────────────────────
export function WellnessRenderer({ content }) {
    const durMatch = content.match(/(\d+)\s*(?:min(?:utes?)?|hrs?|hours?)/i);

    // Detect wellness modality
    const lower = content.toLowerCase();
    let modality = '🧘 Wellness';
    if (lower.includes('meditat')) modality = '🧘 Meditation';
    else if (lower.includes('workout') || lower.includes('exercise')) modality = '💪 Exercise';
    else if (lower.includes('sleep')) modality = '😴 Sleep';
    else if (lower.includes('water') || lower.includes('hydrat')) modality = '💧 Hydration';
    else if (lower.includes('mood') || lower.includes('mental')) modality = '🧠 Mental Wellness';

    return (
        <div className="space-y-3">
            {/* Modality + duration row */}
            <div className="flex flex-wrap gap-2">
                <span className="text-[11px] px-2.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-300 font-medium">
                    {modality}
                </span>
                {durMatch && (
                    <span className="text-[11px] px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-white/50">
                        ⏱️ {durMatch[0]}
                    </span>
                )}
            </div>

            <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>{content}</ReactMarkdown>
            </div>
        </div>
    );
}

// ─── Habit Coach Renderer ─────────────────────────────────────────────────────
export function HabitRenderer({ content }) {
    const freqMatch = content.match(/(?:daily|weekdays|weekends|weekly|every day|each day)/i);
    const catMatch = content.match(/(?:health|productivity|mindfulness|learning|social|self.?care|finance)/i);

    return (
        <div className="space-y-3">
            {/* Frequency/Category badges */}
            <div className="flex flex-wrap gap-2">
                {freqMatch && (
                    <span className="text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 font-medium capitalize">
                        🔁 {freqMatch[0]}
                    </span>
                )}
                {catMatch && (
                    <span className="text-[11px] px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-white/50 capitalize">
                        {catMatch[0]}
                    </span>
                )}
            </div>

            <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>{content}</ReactMarkdown>
            </div>
        </div>
    );
}

// ─── Generic Markdown Fallback ────────────────────────────────────────────────
export function GenericMarkdownRenderer({ content }) {
    return (
        <div className="prose prose-invert prose-sm max-w-none text-white/90 leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>
                {content}
            </ReactMarkdown>
        </div>
    );
}

// ─── Main Router ──────────────────────────────────────────────────────────────
/**
 * Picks the correct renderer based on `agentName`.
 * This is the single entry point used by DraftCard.
 */
const AgentOutputRenderer = ({ content, agentName }) => {
    if (!content) return null;

    const key = detectAgentKey(agentName);

    switch (key) {
        case 'meal_planner': return <MealPlanRenderer content={content} />;
        case 'productivity': return <TaskListRenderer content={content} />;
        case 'study': return <StudyPlanRenderer content={content} />;
        case 'wellness': return <WellnessRenderer content={content} />;
        case 'habit_coach': return <HabitRenderer content={content} />;
        default: return <GenericMarkdownRenderer content={content} />;
    }
};

export default AgentOutputRenderer;
