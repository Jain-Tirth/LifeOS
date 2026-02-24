import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Droplets, Moon, Sun, Plus, Trash2, X, Loader2, Heart, Dumbbell, Brain } from 'lucide-react';
import { getWellnessActivities, logWellnessActivity } from '../../api/wellness';
import { ResponsiveContainer, LineChart, Line, XAxis, Tooltip, BarChart, Bar } from 'recharts';
import { useToast } from '../../context/ToastContext';

import client from '../../api/client';

const deleteWellnessActivity = async (id) => {
    return client.delete(`/wellness-activities/${id}/`);
};

const Wellness = () => {
    const [activities, setActivities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeType, setActiveType] = useState('all');
    const [showAddModal, setShowAddModal] = useState(false);
    const [addForm, setAddForm] = useState({
        activity_type: 'exercise',
        duration: 30,
        notes: '',
        recorded_at: new Date().toISOString().slice(0, 16),
    });
    const [adding, setAdding] = useState(false);
    const toast = useToast();

    useEffect(() => {
        fetchActivities();
    }, []);

    const fetchActivities = async () => {
        setLoading(true);
        try {
            const res = await getWellnessActivities();
            const data = res.data.results || res.data;
            setActivities(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddActivity = async (e) => {
        e.preventDefault();
        setAdding(true);
        try {
            await logWellnessActivity({
                ...addForm,
                duration: parseInt(addForm.duration) || null,
                recorded_at: new Date(addForm.recorded_at).toISOString(),
            });
            toast.success('Activity logged!');
            setShowAddModal(false);
            setAddForm({
                activity_type: 'exercise',
                duration: 30,
                notes: '',
                recorded_at: new Date().toISOString().slice(0, 16),
            });
            fetchActivities();
        } catch (error) {
            console.error(error);
            toast.error('Failed to log activity.');
        } finally {
            setAdding(false);
        }
    };

    const handleDeleteActivity = async (id) => {
        try {
            await deleteWellnessActivity(id);
            toast.success('Activity removed');
            fetchActivities();
        } catch (error) {
            console.error(error);
            toast.error('Failed to delete activity.');
        }
    };

    // Filter
    const filteredActivities = activeType === 'all'
        ? activities
        : activities.filter(a => a.activity_type === activeType);

    // Stats
    const totalActivities = activities.length;
    const totalMinutes = activities.reduce((sum, a) => sum + (a.duration || 0), 0);
    const avgDuration = totalActivities > 0 ? Math.round(totalMinutes / totalActivities) : 0;

    // Build activity distribution
    const typeCount = {};
    activities.forEach(a => {
        typeCount[a.activity_type] = (typeCount[a.activity_type] || 0) + 1;
    });

    // Build daily activity data (last 7 days)
    const last7Days = [];
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const dateStr = d.toISOString().split('T')[0];
        const dayActivities = activities.filter(a => a.recorded_at?.startsWith(dateStr));
        last7Days.push({
            day: d.toLocaleDateString('en-US', { weekday: 'short' }),
            count: dayActivities.length,
            minutes: dayActivities.reduce((sum, a) => sum + (a.duration || 0), 0),
        });
    }

    const activityIcons = {
        exercise: <Dumbbell size={20} />,
        meditation: <Brain size={20} />,
        sleep: <Moon size={20} />,
        hydration: <Droplets size={20} />,
        mood: <Heart size={20} />,
    };

    const activityColors = {
        exercise: 'text-orange-400 bg-orange-500/10',
        meditation: 'text-purple-400 bg-purple-500/10',
        sleep: 'text-indigo-400 bg-indigo-500/10',
        hydration: 'text-teal-400 bg-teal-500/10',
        mood: 'text-pink-400 bg-pink-500/10',
    };

    const types = ['all', 'exercise', 'meditation', 'sleep', 'hydration', 'mood'];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
            <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Wellness</h2>
                    <p className="text-white/60">
                        {totalActivities > 0
                            ? `${totalActivities} activities · ${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}m tracked`
                            : 'Track your health, habits, and mood.'}
                    </p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl transition-colors"
                >
                    <Plus size={20} />
                    <span>Log Activity</span>
                </button>
            </header>

            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Object.entries(typeCount).map(([type, count]) => (
                    <div key={type} className={`p-4 rounded-2xl border border-white/10 ${activityColors[type]?.split(' ')[1] || 'bg-white/5'}`}>
                        <div className="flex items-center gap-2 mb-2">
                            <div className={`p-1.5 rounded-lg ${activityColors[type] || 'text-white/40 bg-white/5'}`}>
                                {activityIcons[type] || <Activity size={16} />}
                            </div>
                        </div>
                        <div className={`text-2xl font-bold font-display ${activityColors[type]?.split(' ')[0] || 'text-white'}`}>{count}</div>
                        <div className="text-xs text-white/40 capitalize">{type}</div>
                    </div>
                ))}
                {totalActivities === 0 && (
                    <div className="col-span-full p-4 rounded-2xl border border-white/10 bg-white/5 text-center text-white/30 text-sm">
                        No activities yet
                    </div>
                )}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Hydration Card */}
                <div className="p-6 rounded-3xl glass-card bg-teal-500/5 border-teal-500/10 relative overflow-hidden group">
                    <div className="relative z-10">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-white">Hydration</h3>
                            <Droplets className="text-teal-400" />
                        </div>
                        <div className="text-4xl font-bold text-white font-display mb-1">
                            {typeCount.hydration || 0}<span className="text-lg text-white/50 ml-1">logs</span>
                        </div>
                        <p className="text-white/40 text-sm">Keep logging to track your intake</p>
                    </div>
                    <div className="absolute bottom-0 left-0 w-full h-24 bg-teal-500/20 rounded-b-3xl transform translate-y-4 group-hover:translate-y-2 transition-transform duration-500">
                        <div className="w-[200%] h-full absolute top-0 left-0 animate-float opacity-50 bg-teal-500/30 blur-xl"></div>
                    </div>
                </div>

                {/* Activity Trend */}
                <div className="p-6 rounded-3xl glass-card bg-teal-500/5 border-teal-500/10 md:col-span-2">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-bold text-white">Weekly Activity</h3>
                        <Sun className="text-yellow-400" />
                    </div>
                    <div className="h-40 w-full">
                        {last7Days.some(d => d.count > 0) ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={last7Days}>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                                        itemStyle={{ color: '#fff' }}
                                        formatter={(value, name) => [value, name === 'minutes' ? 'Minutes' : 'Activities']}
                                    />
                                    <Bar dataKey="minutes" fill="#14B8A6" radius={[4, 4, 0, 0]} />
                                    <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#ffffff60', fontSize: 12 }} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-white/20 text-sm">
                                No activity data in the last 7 days
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Activity Log with Filter */}
            <div className="rounded-3xl glass-card overflow-hidden">
                {/* Filter tabs */}
                <div className="flex border-b border-white/10 overflow-x-auto scrollbar-hide">
                    {types.map(type => (
                        <button
                            key={type}
                            onClick={() => setActiveType(type)}
                            className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors capitalize relative ${activeType === type
                                ? 'text-teal-400 bg-white/5'
                                : 'text-white/40 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            {type === 'all' ? 'All Activities' : type}
                            {activeType === type && (
                                <motion.div
                                    layoutId="wellnessTab"
                                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-400"
                                />
                            )}
                        </button>
                    ))}
                </div>

                <div className="p-6 space-y-4">
                    <h3 className="text-xl font-bold text-white">
                        {activeType === 'all' ? 'All' : activeType.charAt(0).toUpperCase() + activeType.slice(1)} Activities
                        {filteredActivities.length > 0 && <span className="text-sm font-normal text-white/40 ml-2">({filteredActivities.length})</span>}
                    </h3>
                    {loading ? (
                        <div className="text-center text-white/40 flex items-center justify-center gap-2 py-8">
                            <Loader2 size={18} className="animate-spin" />
                            Loading activities...
                        </div>
                    ) : filteredActivities.length === 0 ? (
                        <div className="text-center py-8">
                            <Activity size={40} className="text-white/10 mx-auto mb-3" />
                            <p className="text-white/40">No activities logged yet.</p>
                            <p className="text-white/20 text-sm mt-1">Use the Orchestrator chat or click "Log Activity" to add one.</p>
                        </div>
                    ) : (
                        <AnimatePresence>
                            {filteredActivities.map((activity) => (
                                <motion.div
                                    key={activity.id}
                                    initial={{ opacity: 0, y: 5 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, x: -30 }}
                                    className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 group hover:border-white/10 transition-all"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-full ${activityColors[activity.activity_type] || 'text-white/40 bg-white/5'}`}>
                                            {activityIcons[activity.activity_type] || <Activity size={20} />}
                                        </div>
                                        <div>
                                            <h4 className="text-white font-medium capitalize">{activity.activity_type}</h4>
                                            <p className="text-sm text-white/40 max-w-md truncate">{activity.notes || 'No notes'}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="text-right">
                                            {activity.duration && <div className="text-white font-bold">{activity.duration}m</div>}
                                            <div className="text-xs text-white/40">
                                                {new Date(activity.recorded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleDeleteActivity(activity.id)}
                                            className="opacity-0 group-hover:opacity-100 text-white/20 hover:text-red-400 transition-all p-1"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    )}
                </div>
            </div>

            {/* Add Activity Modal */}
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
                                <h3 className="text-xl font-bold text-white">Log Activity</h3>
                                <button onClick={() => setShowAddModal(false)} className="text-white/40 hover:text-white">
                                    <X size={20} />
                                </button>
                            </div>
                            <form onSubmit={handleAddActivity} className="space-y-4">
                                <div>
                                    <label className="text-sm text-white/60 mb-2 block">Activity Type</label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {['exercise', 'meditation', 'sleep', 'hydration', 'mood'].map(type => (
                                            <button
                                                key={type}
                                                type="button"
                                                onClick={() => setAddForm(p => ({ ...p, activity_type: type }))}
                                                className={`p-3 rounded-xl text-sm font-medium border transition-all capitalize flex flex-col items-center gap-1 ${addForm.activity_type === type
                                                    ? `${activityColors[type]} border-white/20 ring-1 ring-white/10`
                                                    : 'bg-white/5 border-white/10 text-white/40'
                                                    }`}
                                            >
                                                <div className="text-lg">{
                                                    type === 'exercise' ? '🏋️' :
                                                        type === 'meditation' ? '🧘' :
                                                            type === 'sleep' ? '😴' :
                                                                type === 'hydration' ? '💧' : '😊'
                                                }</div>
                                                {type}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Duration (minutes)</label>
                                    <input
                                        type="number"
                                        value={addForm.duration}
                                        onChange={e => setAddForm(p => ({ ...p, duration: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3"
                                        min={0}
                                        placeholder="30"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">When</label>
                                    <input
                                        type="datetime-local"
                                        value={addForm.recorded_at}
                                        onChange={e => setAddForm(p => ({ ...p, recorded_at: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Notes (optional)</label>
                                    <textarea
                                        value={addForm.notes}
                                        onChange={e => setAddForm(p => ({ ...p, notes: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3 resize-none"
                                        rows={3}
                                        placeholder="How did you feel?"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={adding}
                                    className="w-full py-3 bg-teal-600 hover:bg-teal-700 text-white rounded-xl transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {adding ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
                                    {adding ? 'Logging...' : 'Log Activity'}
                                </button>
                            </form>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default Wellness;
