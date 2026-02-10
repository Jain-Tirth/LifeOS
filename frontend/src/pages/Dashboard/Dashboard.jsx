import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    Calendar, 
    Heart, 
    BookOpen, 
    Utensils, 
    ShoppingBag 
} from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts'; // Simple charts for cards
import BentoCard from '../../components/ui/BentoCard';
import { getTasks } from '../../api/tasks';
// Import other APIs as they are implemented

const Dashboard = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState({
        productivity: { value: '0', label: 'Tasks Done' },
        wellness: { value: '0', label: 'Activities' },
        study: { value: '0h', label: 'Focused' },
        meal: { value: '0', label: 'Meals' },
        shopping: { value: '$0', label: 'Spent' }
    });

    useEffect(() => {
        const fetchStats = async () => {
            try {
                // Fetch Productivity Stats
                const tasksRes = await getTasks({ status: 'completed' });
                const completedTasks = tasksRes.data?.length || 0;

                setStats(prev => ({
                    ...prev,
                    productivity: { value: completedTasks.toString(), label: 'Tasks Done' }
                }));

                // Fetch other stats here...
            } catch (error) {
                console.error("Failed to fetch dashboard stats:", error);
            }
        };

        fetchStats();
    }, []);

    const mockChartData = [
        { v: 10 }, { v: 20 }, { v: 15 }, { v: 25 }, { v: 18 }, { v: 30 }, { v: 25 }
    ];

    const TinyChart = ({ color }) => (
        <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mockChartData}>
                <defs>
                    <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="currentColor" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="currentColor" stopOpacity={0}/>
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
                <h2 className="text-4xl font-bold text-white mb-2 font-display">Good Morning, User</h2>
                <p className="text-white/60">Here's your daily overview.</p>
            </header>

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
                     {/* Placeholder for larger chart/ring */}
                     <div className="w-full h-full flex items-center justify-center text-teal-400/30">
                        Work in Progress: Activity Ring
                     </div>
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
                    <TinyChart color="card-productivity" />
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

                 {/* Shopping */}
                 <BentoCard
                    title="Shopping"
                    value={stats.shopping.value}
                    label={stats.shopping.label}
                    icon={ShoppingBag}
                    color="card-shopping"
                    delay={0.4}
                    onClick={() => navigate('/shopping')}
                >
                     <TinyChart color="card-shopping" />
                </BentoCard>
            </div>
        </div>
    );
};

export default Dashboard;
