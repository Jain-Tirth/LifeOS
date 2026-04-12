/**
 * ActionFeedbackBanner — Sprint 3, Mission 3: Action Feedback UX
 *
 * Displays structured action results (auto-saves) that the backend applied
 * after an agent response, giving users transparency about what was persisted.
 *
 * Shows for each action: type, what was saved, its DB ID, and any failure.
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, XCircle, ChevronDown, Database, Zap } from 'lucide-react';

// Maps action name → user-friendly label + color
const ACTION_META = {
    create_task: { label: 'Task saved', color: 'purple', icon: '📋' },
    create_meal_plan: { label: 'Meal plan saved', color: 'emerald', icon: '🍽️' },
    create_study_session: { label: 'Study session saved', color: 'blue', icon: '📚' },
    create_wellness_activity: { label: 'Wellness activity saved', color: 'teal', icon: '🧘' },
    create_habit: { label: 'Habit saved', color: 'amber', icon: '⚡' },
};

const COLOR_MAP = {
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-300',
    emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300',
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-300',
    teal: 'bg-teal-500/10 border-teal-500/20 text-teal-300',
    amber: 'bg-amber-500/10 border-amber-500/20 text-amber-300',
    red: 'bg-red-500/10 border-red-500/20 text-red-300',
};

function ActionRow({ action }) {
    const [expanded, setExpanded] = useState(false);
    const isSuccess = action.status === 'success';
    const meta = ACTION_META[action.action] || { label: action.action, color: 'purple', icon: '✨' };
    const colorClass = isSuccess ? COLOR_MAP[meta.color] : COLOR_MAP.red;

    // Build a human-readable summary
    const savedName = action.result?.title
        || action.result?.meal_name
        || action.result?.subject
        || action.result?.name
        || action.result?.activity_type
        || null;

    return (
        <div className={`rounded-lg border px-3 py-2 text-xs ${colorClass} transition-all`}>
            <div className="flex items-center gap-2">
                <span className="text-base leading-none">{meta.icon}</span>
                <div className="flex-1 min-w-0">
                    <span className="font-semibold">
                        {isSuccess ? meta.label : `Failed: ${meta.label}`}
                    </span>
                    {savedName && (
                        <span className="ml-1 opacity-70 truncate">— {savedName}</span>
                    )}
                    {action.result?.id && isSuccess && (
                        <span className="ml-1 opacity-40">#{action.result.id}</span>
                    )}
                </div>

                {isSuccess
                    ? <CheckCircle2 size={12} className="flex-shrink-0 opacity-70" />
                    : <XCircle size={12} className="flex-shrink-0 opacity-70" />
                }

                {/* Expand for error details or extra fields */}
                {(!isSuccess || (action.result && Object.keys(action.result).length > 2)) && (
                    <button
                        onClick={() => setExpanded(e => !e)}
                        className="opacity-40 hover:opacity-70 transition-opacity flex-shrink-0"
                    >
                        <ChevronDown
                            size={12}
                            className={`transition-transform ${expanded ? 'rotate-180' : ''}`}
                        />
                    </button>
                )}
            </div>

            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="mt-2 font-mono opacity-60 break-all whitespace-pre-wrap">
                            {isSuccess
                                ? JSON.stringify(action.result, null, 2)
                                : action.error || 'Unknown error'
                            }
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

/**
 * @param {Array} actions – array of {action, status, result?, error?} objects
 *                          from the backend `actions_applied` SSE event
 */
const ActionFeedbackBanner = ({ actions }) => {
    if (!actions || actions.length === 0) return null;

    const successCount = actions.filter(a => a.status === 'success').length;
    const failCount = actions.length - successCount;

    return (
        <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="mt-2 space-y-1"
        >
            {/* Summary row */}
            <div className="flex items-center gap-1.5 text-[10px] text-white/30 font-medium uppercase tracking-wider mb-1">
                <Zap size={9} />
                <span>
                    {successCount > 0 && `${successCount} auto-saved`}
                    {successCount > 0 && failCount > 0 && ' · '}
                    {failCount > 0 && <span className="text-red-400/60">{failCount} failed</span>}
                </span>
                <Database size={9} className="ml-auto" />
            </div>

            {actions.map((action, i) => (
                <ActionRow key={i} action={action} />
            ))}
        </motion.div>
    );
};

export default ActionFeedbackBanner;
