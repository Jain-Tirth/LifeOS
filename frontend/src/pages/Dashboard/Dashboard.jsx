import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Calendar,
    Heart,
    BookOpen,
    Utensils,
    ShoppingBag,
    TrendingUp,
    MessageSquare,
    Clock,
    Loader2
} from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer, BarChart, Bar } from 'recharts';
import BentoCard from '../../components/ui/BentoCard';
import { getTasks } from '../../api/tasks';
import { getMealPlans } from '../../api/meals';
import { getStudySessions } from '../../api/study';
import { getWellnessActivities } from '../../api/wellness';
import { useAuth } from '../../context/AuthContext';

const Dashboard = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        productivity: { value: '—', label: 'Tasks' },
        wellness: { value: '—', label: 'Activities' },
        study: { value: '—', label: 'Sessions' },
        meal: { value: '—', label: 'Meals' },
    });
    const [recentTasks, setRecentTasks] = useState([]);
    const [taskChartData, setTaskChartData] = useState([]);
    const [wellnessChartData, setWellnessChartData] = useState([]);

    // Greeting based on time
    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return 'Good Morning';
        if (hour < 17) return 'Good Afternoon';
        return 'Good Evening';
    };

    useEffect(() => {
        const fetchAllStats = async () => {
            setLoading(true);
            try {
                // Fetch all data in parallel
                const [tasksRes, mealsRes, studyRes, wellnessRes] = await Promise.allSettled([
                    getTasks({}),
                    getMealPlans({}),
                    getStudySessions(),
                    getWellnessActivities({}),
                ]);

                // Tasks
                const allTasks = tasksRes.status === 'fulfilled'
                    ? (tasksRes.value.data.results || tasksRes.value.data || [])
                    : [];
                const completedTasks = allTasks.filter(t => t.status === 'completed').length;
                const totalTasks = allTasks.length;
                setRecentTasks(allTasks.filter(t => t.status !== 'completed').slice(0, 4));

                // Meals
                const allMeals = mealsRes.status === 'fulfilled'
                    ? (mealsRes.value.data.results || mealsRes.value.data || [])
                    : [];

                // Study
                const allStudy = studyRes.status === 'fulfilled'
                    ? (studyRes.value.data.results || studyRes.value.data || [])
                    : [];
                const totalStudyMinutes = allStudy.reduce((sum, s) => sum + (s.duration || 0), 0);
                const totalStudyHours = Math.floor(totalStudyMinutes / 60);

                // Wellness
                const allWellness = wellnessRes.status === 'fulfilled'
                    ? (wellnessRes.value.data.results || wellnessRes.value.data || [])
                    : [];

                setStats({
                    productivity: { value: `${completedTasks}/${totalTasks}`, label: 'Tasks Done' },
                    wellness: { value: String(allWellness.length), label: 'Activities' },
                    study: { value: `${totalStudyHours}h`, label: 'Focused' },
                    meal: { value: String(allMeals.length), label: 'Meals' },
                });

                // Build mini chart data
                const last7 = [];
                for (let i = 6; i >= 0; i--) {
                    const d = new Date();
                    d.setDate(d.getDate() - i);
                    const dateStr = d.toISOString().split('T')[0];
                    last7.push({
                        day: d.toLocaleDateString('en-US', { weekday: 'short' }),
                        tasks: allTasks.filter(t => t.created_at?.startsWith(dateStr)).length,
                        wellness: allWellness.filter(w => w.recorded_at?.startsWith(dateStr)).length,
                    });
                }
                setTaskChartData(last7.map(d => ({ v: d.tasks || Math.random() * 3 })));
                setWellnessChartData(last7.map(d => ({ v: d.wellness || Math.random() * 2 })));

            } catch (error) {
                console.error("Failed to fetch dashboard stats:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchAllStats();
    }, []);

    const TinyChart = ({ color, data }) => (
        <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data || [{ v: 1 }, { v: 2 }, { v: 1 }, { v: 3 }, { v: 2 }]}>
                <defs>
                    <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="currentColor" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="currentColor" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <Area
                    type="monotone"
                    dataKey="v"
                    stroke="currentColor"
                    fillOpacity={1}
                    fill={`url(#gradient-${color})`}
                    strokeWidth={2}
                    className={
                        color === 'card-productivity' ? 'text-purple-400' :
                            color === 'card-wellness' ? 'text-teal-400' :
                                color === 'card-study' ? 'text-blue-400' :
                                    color === 'card-meal' ? 'text-green-400' :
                                        color === 'card-shopping' ? 'text-amber-400' :
                                            'text-gray-400'
                    }
                />
            </AreaChart>
        </ResponsiveContainer>
    );

    return (
        <div className="space-y-8">
            <header className="mb-10">
                <motion.h2
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-4xl font-bold text-white mb-2 font-display"
                >
                    {getGreeting()}, {user?.first_name || 'User'}
                </motion.h2>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="text-white/60"
                >
                    {loading ? 'Loading your overview...' : "Here's your daily overview."}
                </motion.p>
            </header>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 size={32} className="animate-spin text-white/30" />
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 auto-rows-[200px]">
                        {/* Wellness - Large Card */}
                        <BentoCard
                            title="Wellness"
                            value={stats.wellness.value}
                            label={stats.wellness.label}
                            icon={Heart}
                            color="card-wellness"
                            className="md:col-span-2 md:row-span-2"
                            onClick={() => navigate('/wellness')}
                        >
                            <TinyChart color="card-wellness" data={wellnessChartData} />
                        </BentoCard>

                        {/* Productivity */}
                        <BentoCard
                            title="Productivity"
                            value={stats.productivity.value}
                            label={stats.productivity.label}
                            icon={Calendar}
                            color="card-productivity"
                            delay={0.1}
                            onClick={() => navigate('/productivity')}
                        >
                            <TinyChart color="card-productivity" data={taskChartData} />
                        </BentoCard>

                        {/* Study */}
                        <BentoCard
                            title="Study Buddy"
                            value={stats.study.value}
                            label={stats.study.label}
                            icon={BookOpen}
                            color="card-study"
                            delay={0.2}
                            onClick={() => navigate('/study')}
                        >
                            <TinyChart color="card-study" />
                        </BentoCard>

                        {/* Meal Planner */}
                        <BentoCard
                            title="Meal Planner"
                            value={stats.meal.value}
                            label={stats.meal.label}
                            icon={Utensils}
                            color="card-meal"
                            delay={0.3}
                            onClick={() => navigate('/meals')}
                        >
                            <TinyChart color="card-meal" />
                        </BentoCard>

                        {/* Orchestrator Quick Access */}
                        <BentoCard
                            title="Orchestrator"
                            value="AI"
                            label="Command Center"
                            icon={MessageSquare}
                            color="card-shopping"
                            delay={0.4}
                            onClick={() => navigate('/chat')}
                        >
                            <TinyChart color="card-shopping" />
                        </BentoCard>
                    </div>

                    {/* Quick Tasks */}
                    {recentTasks.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                            className="rounded-3xl glass-card p-6"
                        >
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-xl font-bold text-white">Upcoming Tasks</h3>
                                <button
                                    onClick={() => navigate('/productivity')}
                                    className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
                                >
                                    View all →
                                </button>
                            </div>
                            <div className="space-y-2">
                                {recentTasks.map(task => (
                                    <div
                                        key={task.id}
                                        className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                                        onClick={() => navigate('/productivity')}
                                    >
                                        <div className={`w-2 h-2 rounded-full ${task.priority === 'urgent' ? 'bg-red-400' :
                                            task.priority === 'high' ? 'bg-orange-400' :
                                                task.priority === 'medium' ? 'bg-yellow-400' : 'bg-blue-400'
                                            }`} />
                                        <span className="text-white font-medium flex-1 truncate">{task.title}</span>
                                        <span className="text-xs text-white/30 capitalize">{task.priority}</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </>
            )}
        </div>
    );
};

export default Dashboard;
