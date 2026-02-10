import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Droplets, Moon, Sun, Plus } from 'lucide-react';
import { getWellnessActivities, logWellnessActivity } from '../../api/wellness';
import { ResponsiveContainer, LineChart, Line, XAxis, Tooltip } from 'recharts';

const Wellness = () => {
    const [activities, setActivities] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchActivities();
    }, []);

    const fetchActivities = async () => {
        try {
            const res = await getWellnessActivities();
            // Handle pagination or direct array
            const data = res.data.results || res.data;
            setActivities(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    // Mock data for waves/charts
    const moodData = [
        { day: 'Mon', value: 3 },
        { day: 'Tue', value: 4 },
        { day: 'Wed', value: 2 },
        { day: 'Thu', value: 5 },
        { day: 'Fri', value: 4 },
        { day: 'Sat', value: 5 },
        { day: 'Sun', value: 4 },
    ];

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
             <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Wellness</h2>
                    <p className="text-white/60">Track your health, habits, and mood.</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl transition-colors">
                    <Plus size={20} />
                    <span>Log Activity</span>
                </button>
            </header>

            {/* Top Visuals */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Hydration Wave Mock */}
                <div className="p-6 rounded-3xl glass-card bg-teal-500/5 border-teal-500/10 relative overflow-hidden group">
                    <div className="relative z-10">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-white">Hydration</h3>
                            <Droplets className="text-teal-400" />
                        </div>
                        <div className="text-4xl font-bold text-white font-display mb-1">1,250<span className="text-lg text-white/50 ml-1">ml</span></div>
                        <p className="text-white/40 text-sm">Goal: 2,500ml</p>
                    </div>
                    {/* Abstract Wave Animation */}
                    <div className="absolute bottom-0 left-0 w-full h-24 bg-teal-500/20 rounded-b-3xl transform translate-y-4 group-hover:translate-y-2 transition-transform duration-500">
                        <div className="w-[200%] h-full absolute top-0 left-0 animate-float opacity-50 bg-teal-500/30 blur-xl"></div>
                    </div>
                </div>

                {/* Mood Chart */}
                <div className="p-6 rounded-3xl glass-card bg-teal-500/5 border-teal-500/10 md:col-span-2">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-bold text-white">Mood Trend</h3>
                        <Sun className="text-yellow-400" />
                    </div>
                    <div className="h-40 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={moodData}>
                                <Tooltip 
                                    contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Line 
                                    type="monotone" 
                                    dataKey="value" 
                                    stroke="#14B8A6" 
                                    strokeWidth={3} 
                                    dot={{ r: 4, fill: '#14B8A6', strokeWidth: 0 }} 
                                />
                                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#ffffff60' }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Activity Log */}
            <div className="rounded-3xl glass-card p-6">
                <h3 className="text-xl font-bold text-white mb-6">Recent Activities</h3>
                <div className="space-y-4">
                    {loading ? (
                         <div className="text-center text-white/40">Loading activities...</div>
                    ) : activities.length === 0 ? (
                        <div className="text-center text-white/40">No activities logged yet.</div>
                    ) : (
                        activities.map((activity) => (
                            <div key={activity.id} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 rounded-full bg-teal-500/10 text-teal-400">
                                        {activity.activity_type === 'meditation' ? <Moon size={20} /> : <Activity size={20} />}
                                    </div>
                                    <div>
                                        <h4 className="text-white font-medium capitalize">{activity.activity_type}</h4>
                                        <p className="text-sm text-white/40">{activity.notes || 'No notes'}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-white font-bold">{activity.duration}m</div>
                                    <div className="text-xs text-white/40">
                                        {new Date(activity.recorded_at).toLocaleDateString()}
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

export default Wellness;
