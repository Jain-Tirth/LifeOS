import React, { useState } from 'react';
import { Check, Sparkles, Loader2, Save, ChevronDown, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { saveAgentResponse } from '../../api/chat';
import { useToast } from '../../context/ToastContext';
import { AGENT_META, detectAgentKey, buildSavePayload } from '../../utils/agentParsers';
import MessageActions from '../MessageActions/MessageActions';
import AgentOutputRenderer from '../AgentOutputRenderer/AgentOutputRenderer';
import ActionFeedbackBanner from '../ActionFeedbackBanner/ActionFeedbackBanner';

const ACCENT_MAP = {
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

/**
 * DraftCard — Renders an agent response using the schema-driven AgentOutputRenderer.
 *
 * Sprint 3 changes:
 *  - Content is now rendered by AgentOutputRenderer (schema-driven, per-agent UI)
 *    instead of a single generic ReactMarkdown block.
 *  - Action feedback (actionsApplied) is rendered via ActionFeedbackBanner when
 *    the backend auto-saved structured records from the response.
 */
const DraftCard = ({
    content,
    agentName,
    timestamp,
    sessionId,
    msgIndex,
    isSaved,
    onMarkSaved,
    onCopy,
    onDelete,
    formatTimestamp,
    actionsApplied,   // Sprint 3: Action Feedback UX
}) => {
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(isSaved || false);
    const [showDetails, setShowDetails] = useState(false);
    const navigate = useNavigate();
    const toast = useToast();

    const agentKey = detectAgentKey(agentName);
    const meta = agentKey ? AGENT_META[agentKey] : null;
    const isActionable = content && (content.includes('-') || content.includes('\n') || content.length > 80);
    const previewPayload = agentKey ? buildSavePayload(agentKey, content) : null;
    const accent = meta ? ACCENT_MAP[meta.color] : ACCENT_MAP.purple;

    const handleSave = async () => {
        setSaving(true);
        try {
            const payload = buildSavePayload(agentKey || null, content);
            await saveAgentResponse({
                agent_type: payload.agent_type,
                session_id: sessionId,
                data: payload.data,
            });
            setSaved(true);
            onMarkSaved?.(msgIndex);
            toast.success(`Saved to ${meta?.label || 'Tasks'}!`);
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

    return (
        <div className={`bg-gradient-to-br ${accent.bg} ${accent.border} border rounded-2xl p-5 mt-2 group transition-all duration-300`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white/50">
                    {meta ? (
                        <span className="text-sm">{meta.icon || <Sparkles size={12} className="text-yellow-400" />}</span>
                    ) : (
                        <Sparkles size={12} className="text-yellow-400" />
                    )}
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
                    <MessageActions message={content} onCopy={onCopy} onDelete={onDelete} />
                </div>
            </div>

            {/* Sprint 3 Mission 2: Schema-driven rendering */}
            <div className="mb-4">
                <AgentOutputRenderer content={content} agentName={agentName} />
            </div>

            {/* Sprint 3 Mission 3: Action Feedback UX — auto-save results */}
            {actionsApplied && actionsApplied.length > 0 && (
                <ActionFeedbackBanner actions={actionsApplied} />
            )}

            {/* Save Data Preview (manual save) */}
            {isActionable && previewPayload && !saved && !actionsApplied?.length && (
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

            {/* Action Buttons (only show manual save if no auto-actions applied) */}
            {isActionable && !actionsApplied?.length && (
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

            {/* If actions were auto-applied, show a "View in [section]" shortcut */}
            {actionsApplied?.length > 0 && meta && (
                <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    onClick={() => navigate(meta.route)}
                    className="mt-2 flex items-center gap-2 text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                    <ExternalLink size={11} />
                    View in {meta.label}
                </motion.button>
            )}
        </div>
    );
};

export default DraftCard;
