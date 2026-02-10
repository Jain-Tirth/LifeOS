import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Circle, Plus, AlertCircle, Clock } from 'lucide-react';
import { getTasks, updateTask, createTask } from '../../api/tasks';

const Productivity = () => {
    const [tasks, setTasks] = useState([]);
    const [filter, setFilter] = useState('todo'); // todo, in_progress, completed
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchTasks();
    }, [filter]);

    const fetchTasks = async () => {
        setLoading(true);
        try {
            const res = await getTasks({ status: filter });
            // Handle pagination or direct array
            const data = res.data.results || res.data;
            setTasks(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleStatus = async (task) => {
        const newStatus = task.status === 'completed' ? 'todo' : 'completed';
        try {
            await updateTask(task.id, { status: newStatus });
            fetchTasks(); // Refresh
        } catch (error) {
            console.error(error);
        }
    };

    const priorityColors = {
        low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
        medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
        high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
        urgent: 'bg-red-500/10 text-red-400 border-red-500/20',
    };

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
            <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Productivity</h2>
                    <p className="text-white/60">Manage your tasks and focus.</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl transition-colors">
                    <Plus size={20} />
                    <span>New Task</span>
                </button>
            </header>

            {/* Matrix / Kanban Placeholder */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-6 rounded-3xl glass-card bg-purple-500/5 border-purple-500/10">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold text-white">Focus Timer</h3>
                        <Clock className="text-purple-400" />
                    </div>
                    <div className="text-center py-10">
                        <div className="text-6xl font-bold text-white font-display text-glow mb-4">25:00</div>
                        <p className="text-white/40">Pomodoro Status: Ready</p>
                         <button className="mt-6 px-8 py-3 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors">
                            Start Focus
                        </button>
                    </div>
                </div>

                <div className="p-6 rounded-3xl glass-card bg-purple-500/5 border-purple-500/10">
                    <h3 className="text-xl font-bold text-white mb-6">Priority Matrix</h3>
                     <div className="grid grid-cols-2 gap-4 h-64">
                        <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/10 flex flex-col items-center justify-center">
                            <span className="text-red-400 font-bold text-lg">Do First</span>
                            <span className="text-white/40 text-sm">Urgent & Important</span>
                        </div>
                        <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/10 flex flex-col items-center justify-center">
                            <span className="text-blue-400 font-bold text-lg">Schedule</span>
                             <span className="text-white/40 text-sm">Not Urgent & Important</span>
                        </div>
                        <div className="bg-yellow-500/10 rounded-xl p-4 border border-yellow-500/10 flex flex-col items-center justify-center">
                            <span className="text-yellow-400 font-bold text-lg">Delegate</span>
                             <span className="text-white/40 text-sm">Urgent & Not Important</span>
                        </div>
                         <div className="bg-gray-500/10 rounded-xl p-4 border border-gray-500/10 flex flex-col items-center justify-center">
                            <span className="text-gray-400 font-bold text-lg">Don't Do</span>
                             <span className="text-white/40 text-sm">Not Urgent & Not Important</span>
                        </div>
                     </div>
                </div>
            </div>

            {/* Task List */}
            <div className="rounded-3xl glass-card overflow-hidden">
                <div className="flex border-b border-white/10">
                    {['todo', 'in_progress', 'completed'].map((s) => (
                        <button
                            key={s}
                            onClick={() => setFilter(s)}
                            className={`flex-1 py-4 text-center font-medium transition-colors ${
                                filter === s ? 'text-purple-400 bg-white/5' : 'text-white/40 hover:text-white hover:bg-white/5'
                            }`}
                        >
                            {s.replace('_', ' ').charAt(0).toUpperCase() + s.slice(1).replace('_', ' ')}
                        </button>
                    ))}
                </div>

                <div className="divide-y divide-white/10">
                    {loading ? (
                        <div className="p-8 text-center text-white/40">Loading tasks...</div>
                    ) : tasks.length === 0 ? (
                        <div className="p-8 text-center text-white/40">
                            No tasks found in this category.
                        </div>
                    ) : (
                        tasks.map((task) => (
                            <div key={task.id} className="p-4 flex items-center gap-4 hover:bg-white/5 transition-colors group">
                                <button 
                                    onClick={() => handleToggleStatus(task)}
                                    className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                                        task.status === 'completed' 
                                            ? 'bg-purple-500 border-purple-500 text-white' 
                                            : 'border-white/20 text-transparent hover:border-purple-500'
                                    }`}
                                >
                                    <CheckCircle size={14} fill="currentColor" />
                                </button>
                                
                                <div className="flex-1 min-w-0">
                                    <h4 className={`text-white font-medium truncate ${task.status === 'completed' ? 'line-through text-white/40' : ''}`}>
                                        {task.title}
                                    </h4>
                                    <p className="text-sm text-white/40 truncate">{task.description}</p>
                                </div>

                                <div className={`px-3 py-1 rounded-full text-xs font-medium border ${priorityColors[task.priority] || priorityColors.medium}`}>
                                    {task.priority}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </motion.div>
    );
};

export default Productivity;
