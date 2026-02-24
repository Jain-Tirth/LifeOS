import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, PieChart, Clock, Hash, Plus, Trash2, X, Loader2, ChevronDown } from 'lucide-react';
import { getStudySessions, createStudySession } from '../../api/study';
import { PieChart as RePieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useToast } from '../../context/ToastContext';

import client from '../../api/client';

const deleteStudySession = async (id) => {
    return client.delete(`/study-sessions/${id}/`);
};

const Study = () => {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [addForm, setAddForm] = useState({ subject: '', topic: '', duration: 60, notes: '' });
    const [adding, setAdding] = useState(false);
    const [expandedSession, setExpandedSession] = useState(null);
    const toast = useToast();

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        setLoading(true);
        try {
            const res = await getStudySessions();
            const data = res.data.results || res.data;
            setSessions(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddSession = async (e) => {
        e.preventDefault();
        if (!addForm.subject.trim()) return;
        setAdding(true);
        try {
            await createStudySession({
                ...addForm,
                duration: parseInt(addForm.duration) || 60,
            });
            toast.success('Study session logged!');
            setShowAddModal(false);
            setAddForm({ subject: '', topic: '', duration: 60, notes: '' });
            fetchSessions();
        } catch (error) {
            console.error(error);
            toast.error('Failed to log session.');
        } finally {
            setAdding(false);
        }
    };

    const handleDeleteSession = async (id) => {
        try {
            await deleteStudySession(id);
            toast.success('Session removed');
            fetchSessions();
        } catch (error) {
            console.error(error);
            toast.error('Failed to delete session.');
        }
    };

    // Build real chart data from sessions
    const subjectMap = {};
    sessions.forEach(s => {
        subjectMap[s.subject] = (subjectMap[s.subject] || 0) + (s.duration || 0);
    });
    const subjectData = Object.entries(subjectMap)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 6);

    const COLORS = ['#3B82F6', '#60A5FA', '#93C5FD', '#1d4ed8', '#818CF8', '#A78BFA'];

    const totalMinutes = sessions.reduce((sum, s) => sum + (s.duration || 0), 0);
    const totalHours = Math.floor(totalMinutes / 60);
    const remainingMinutes = totalMinutes % 60;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
            <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Study Buddy</h2>
                    <p className="text-white/60">
                        {sessions.length > 0
                            ? `${sessions.length} session${sessions.length === 1 ? '' : 's'} logged · ${totalHours}h ${remainingMinutes}m total`
                            : 'Log sessions and track focus.'}
                    </p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors"
                >
                    <Plus size={20} />
                    <span>Log Session</span>
                </button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Focus Distribution - Real Data */}
                <div className="p-6 rounded-3xl glass-card bg-blue-500/5 border-blue-500/10">
                    <h3 className="text-xl font-bold text-white mb-6">Subject Distribution</h3>
                    <div className="h-64 relative">
                        {subjectData.length > 0 ? (
                            <>
                                <ResponsiveContainer width="100%" height="100%">
                                    <RePieChart>
                                        <Pie
                                            data={subjectData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={80}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {subjectData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                                            itemStyle={{ color: '#fff' }}
                                            formatter={(value) => `${value} min`}
                                        />
                                    </RePieChart>
                                </ResponsiveContainer>
                                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                    <div className="text-center">
                                        <span className="block text-3xl font-bold text-white">{totalHours}h</span>
                                        <span className="text-xs text-white/50">Total</span>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="h-full flex items-center justify-center text-white/20">
                                <div className="text-center">
                                    <PieChart size={40} className="mx-auto mb-2" />
                                    <p className="text-sm">No data yet</p>
                                </div>
                            </div>
                        )}
                    </div>
                    {/* Legend */}
                    {subjectData.length > 0 && (
                        <div className="flex flex-wrap gap-3 mt-4 justify-center">
                            {subjectData.map((entry, i) => (
                                <div key={entry.name} className="flex items-center gap-1.5 text-xs text-white/60">
                                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                                    {entry.name}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Quick Stats */}
                <div className="p-6 rounded-3xl glass-card bg-blue-500/5 border-blue-500/10 flex flex-col">
                    <h3 className="text-xl font-bold text-white mb-6">Study Stats</h3>
                    <div className="grid grid-cols-2 gap-4 flex-1">
                        <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/10 flex flex-col items-center justify-center">
                            <span className="text-3xl font-bold text-blue-400 font-display">{sessions.length}</span>
                            <span className="text-xs text-white/40 mt-1">Sessions</span>
                        </div>
                        <div className="p-4 rounded-2xl bg-purple-500/10 border border-purple-500/10 flex flex-col items-center justify-center">
                            <span className="text-3xl font-bold text-purple-400 font-display">{totalHours}h</span>
                            <span className="text-xs text-white/40 mt-1">Total Time</span>
                        </div>
                        <div className="p-4 rounded-2xl bg-teal-500/10 border border-teal-500/10 flex flex-col items-center justify-center">
                            <span className="text-3xl font-bold text-teal-400 font-display">{Object.keys(subjectMap).length}</span>
                            <span className="text-xs text-white/40 mt-1">Subjects</span>
                        </div>
                        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/10 flex flex-col items-center justify-center">
                            <span className="text-3xl font-bold text-amber-400 font-display">
                                {sessions.length > 0 ? Math.round(totalMinutes / sessions.length) : 0}m
                            </span>
                            <span className="text-xs text-white/40 mt-1">Avg Duration</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Session Timeline */}
            <div className="rounded-3xl glass-card p-6">
                <h3 className="text-xl font-bold text-white mb-6">Recent Sessions</h3>
                <div className="space-y-6">
                    {loading ? (
                        <div className="text-center text-white/40 flex items-center justify-center gap-2">
                            <Loader2 size={18} className="animate-spin" />
                            Loading sessions...
                        </div>
                    ) : sessions.length === 0 ? (
                        <div className="text-center py-8">
                            <BookOpen size={40} className="text-white/10 mx-auto mb-3" />
                            <p className="text-white/40">No study sessions logged yet.</p>
                            <p className="text-white/20 text-sm mt-1">Use the Orchestrator chat or click "Log Session" to add one.</p>
                        </div>
                    ) : (
                        sessions.map((session, idx) => (
                            <motion.div
                                key={session.id || idx}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.05 }}
                                className="relative pl-8 border-l-2 border-white/10 pb-6 last:pb-0 group"
                            >
                                <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-blue-500 border-4 border-slate-900"></div>
                                <div className="flex justify-between items-start">
                                    <div
                                        className="flex-1 cursor-pointer"
                                        onClick={() => setExpandedSession(expandedSession === (session.id || idx) ? null : (session.id || idx))}
                                    >
                                        <span className="text-xs text-blue-400 font-bold uppercase tracking-wider">{session.subject}</span>
                                        <h4 className="text-white font-medium mt-1">{session.topic || 'General Study'}</h4>
                                        {session.created_at && (
                                            <span className="text-xs text-white/30 mt-0.5 block">
                                                {new Date(session.created_at).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                                            </span>
                                        )}
                                        <AnimatePresence>
                                            {expandedSession === (session.id || idx) && session.notes && (
                                                <motion.div
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: 'auto', opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    className="overflow-hidden"
                                                >
                                                    <p className="text-white/40 text-sm mt-2 p-3 bg-white/5 rounded-lg whitespace-pre-wrap">
                                                        {session.notes.slice(0, 500)}
                                                        {session.notes.length > 500 && '...'}
                                                    </p>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="flex items-center gap-2 text-white/50 bg-white/5 px-3 py-1 rounded-full text-sm">
                                            <Clock size={14} />
                                            <span>{session.duration}m</span>
                                        </div>
                                        <button
                                            onClick={() => handleDeleteSession(session.id)}
                                            className="opacity-0 group-hover:opacity-100 text-white/20 hover:text-red-400 transition-all p-1"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        ))
                    )}
                </div>
            </div>

            {/* Add Study Session Modal */}
            <AnimatePresence>
                {showAddModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                        onClick={(e) => e.target === e.currentTarget && setShowAddModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="w-full max-w-md rounded-3xl glass-card p-6"
                        >
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-xl font-bold text-white">Log Study Session</h3>
                                <button onClick={() => setShowAddModal(false)} className="text-white/40 hover:text-white">
                                    <X size={20} />
                                </button>
                            </div>
                            <form onSubmit={handleAddSession} className="space-y-4">
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Subject</label>
                                    <input
                                        type="text"
                                        value={addForm.subject}
                                        onChange={e => setAddForm(p => ({ ...p, subject: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3"
                                        placeholder="e.g., Data Structures"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Topic (optional)</label>
                                    <input
                                        type="text"
                                        value={addForm.topic}
                                        onChange={e => setAddForm(p => ({ ...p, topic: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3"
                                        placeholder="e.g., Binary Trees"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Duration (minutes)</label>
                                    <input
                                        type="number"
                                        value={addForm.duration}
                                        onChange={e => setAddForm(p => ({ ...p, duration: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3"
                                        min={1}
                                        placeholder="60"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Notes (optional)</label>
                                    <textarea
                                        value={addForm.notes}
                                        onChange={e => setAddForm(p => ({ ...p, notes: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3 resize-none"
                                        rows={3}
                                        placeholder="Key takeaways..."
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={adding}
                                    className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {adding ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
                                    {adding ? 'Logging...' : 'Log Session'}
                                </button>
                            </form>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default Study;
