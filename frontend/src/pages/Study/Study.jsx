import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, PieChart, Clock, Hash, Plus } from 'lucide-react';
import { getStudySessions } from '../../api/study';
import { PieChart as RePieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const Study = () => {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        try {
            const res = await getStudySessions();
            // Handle pagination or direct array
            const data = res.data.results || res.data;
            setSessions(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    // Derived Data for Charts
    const subjectData = [
        { name: 'Math', value: 400 },
        { name: 'Physics', value: 300 },
        { name: 'History', value: 200 },
        { name: 'CS', value: 500 },
    ];
    const COLORS = ['#3B82F6', '#60A5FA', '#93C5FD', '#1d4ed8'];

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
             <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Study Buddy</h2>
                    <p className="text-white/60">Log sessions and track focus.</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors">
                    <Plus size={20} />
                    <span>Log Session</span>
                </button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Focus Distribution */}
                <div className="p-6 rounded-3xl glass-card bg-blue-500/5 border-blue-500/10">
                    <h3 className="text-xl font-bold text-white mb-6">Subject Distribution</h3>
                    <div className="h-64 relative">
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
                                />
                            </RePieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="text-center">
                                <span className="block text-3xl font-bold text-white">24h</span>
                                <span className="text-xs text-white/50">Total</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Flashcards Mock */}
                <div className="p-6 rounded-3xl glass-card bg-blue-500/5 border-blue-500/10 flex flex-col justify-between">
                    <div>
                        <h3 className="text-xl font-bold text-white mb-2">Active Recall</h3>
                        <p className="text-white/40 mb-6">Review your recent tricky concepts.</p>
                    </div>
                    
                    <div className="flex-1 flex items-center justify-center p-8 bg-white/5 rounded-2xl border border-white/10 cursor-pointer hover:bg-white/10 transition-colors group relative perspective">
                         <div className="text-center">
                            <h4 className="text-lg font-medium text-white mb-2">What is the Time Complexity of QuickSort?</h4>
                            <p className="text-blue-400 group-hover:opacity-100 opacity-0 transition-opacity">Click to reveal</p>
                         </div>
                    </div>
                </div>
            </div>

            {/* Session Timeline */}
            <div className="rounded-3xl glass-card p-6">
                 <h3 className="text-xl font-bold text-white mb-6">Recent Sessions</h3>
                 <div className="space-y-6">
                    {loading ? (
                         <div className="text-center text-white/40">Loading sessions...</div>
                    ) : sessions.length === 0 ? (
                         <div className="text-center text-white/40">No study sessions logged.</div>
                    ) : (
                        sessions.map((session, idx) => (
                            <div key={idx} className="relative pl-8 border-l-2 border-white/10 pb-6 last:pb-0">
                                <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-blue-500 border-4 border-slate-900"></div>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <span className="text-xs text-blue-400 font-bold uppercase tracking-wider">{session.subject}</span>
                                        <h4 className="text-white font-medium mt-1">{session.topic || 'General Study'}</h4>
                                        {session.notes && <p className="text-white/40 text-sm mt-2 p-3 bg-white/5 rounded-lg">{session.notes}</p>}
                                    </div>
                                    <div className="flex items-center gap-2 text-white/50 bg-white/5 px-3 py-1 rounded-full text-sm">
                                        <Clock size={14} />
                                        <span>{session.duration}m</span>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                 </div>
            </div>
        </motion.div>
    );
};

export default Study;
