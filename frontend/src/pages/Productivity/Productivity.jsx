import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Circle, Plus, AlertCircle, Clock, Trash2, X, Loader2, MoreVertical, Edit2, Play, Pause, RotateCcw } from 'lucide-react';
import { getTasks, updateTask, createTask, deleteTask } from '../../api/tasks';
import { useToast } from '../../context/ToastContext';

const Productivity = () => {
    const [tasks, setTasks] = useState([]);
    const [allTasks, setAllTasks] = useState([]); // unfiltered for stats
    const [filter, setFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [addForm, setAddForm] = useState({ title: '', description: '', priority: 'medium', status: 'todo' });
    const [adding, setAdding] = useState(false);
    const [expandedTask, setExpandedTask] = useState(null);
    const toast = useToast();

    // Timer States
    const [timerActive, setTimerActive] = useState(false);
    const [focusDuration, setFocusDuration] = useState(25 * 60); // default 25 mins
    const [focusTime, setFocusTime] = useState(25 * 60);

    useEffect(() => {
        let interval = null;
        if (timerActive && focusTime > 0) {
            interval = setInterval(() => {
                setFocusTime((time) => time - 1);
            }, 1000);
        } else if (focusTime === 0 && timerActive) {
            setTimerActive(false);
            toast.success('Focus session complete! Take a break.');
            // Reset to selected duration on complete
            setFocusTime(focusDuration);
        }
        return () => clearInterval(interval);
    }, [timerActive, focusTime, focusDuration, toast]);

    const toggleTimer = () => {
        setTimerActive(!timerActive);
    };

    const resetTimer = () => {
        setTimerActive(false);
        setFocusTime(focusDuration);
    };

    const handleDurationChange = (e) => {
        const newDuration = parseInt(e.target.value, 10) * 60;
        setFocusDuration(newDuration);
        setFocusTime(newDuration);
        setTimerActive(false);
    };

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    useEffect(() => {
        fetchAllTasks();
    }, []);

    useEffect(() => {
        fetchTasks();
    }, [filter]);

    const fetchAllTasks = async () => {
        try {
            const res = await getTasks({});
            const data = res.data.results || res.data;
            setAllTasks(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
        }
    };

    const fetchTasks = async () => {
        setLoading(true);
        try {
            const params = filter === 'all' ? {} : { status: filter };
            const res = await getTasks(params);
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
            toast.success(newStatus === 'completed' ? '✅ Task completed!' : 'Task reopened');
            fetchTasks();
            fetchAllTasks();
        } catch (error) {
            console.error(error);
            toast.error('Failed to update task.');
        }
    };

    const handleDeleteTask = async (taskId) => {
        try {
            await deleteTask(taskId);
            toast.success('Task deleted');
            fetchTasks();
            fetchAllTasks();
        } catch (error) {
            console.error(error);
            toast.error('Failed to delete task.');
        }
    };

    const handleAddTask = async (e) => {
        e.preventDefault();
        if (!addForm.title.trim()) return;
        setAdding(true);
        try {
            await createTask(addForm);
            toast.success('Task created!');
            setShowAddModal(false);
            setAddForm({ title: '', description: '', priority: 'medium', status: 'todo' });
            fetchTasks();
            fetchAllTasks();
        } catch (error) {
            console.error(error);
            toast.error('Failed to create task.');
        } finally {
            setAdding(false);
        }
    };

    // Stats
    const totalTasks = allTasks.length;
    const completedTasks = allTasks.filter(t => t.status === 'completed').length;
    const inProgressTasks = allTasks.filter(t => t.status === 'in_progress').length;
    const urgentTasks = allTasks.filter(t => t.priority === 'urgent' && t.status !== 'completed').length;

    const priorityColors = {
        low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
        medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
        high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
        urgent: 'bg-red-500/10 text-red-400 border-red-500/20',
    };

    const priorityDot = {
        low: 'bg-blue-400',
        medium: 'bg-yellow-400',
        high: 'bg-orange-400',
        urgent: 'bg-red-400',
    };

    const filterTabs = [
        { key: 'all', label: 'All' },
        { key: 'todo', label: 'To Do' },
        { key: 'in_progress', label: 'In Progress' },
        { key: 'completed', label: 'Completed' },
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8 scroll-gpu"
        >
            <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Productivity</h2>
                    <p className="text-white/60">
                        {totalTasks > 0
                            ? `${completedTasks}/${totalTasks} tasks completed`
                            : 'Manage your tasks and focus.'}
                    </p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl transition-colors"
                >
                    <Plus size={20} />
                    <span>New Task</span>
                </button>
            </header>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total', value: totalTasks, color: 'text-white', bgColor: 'bg-white/5 border-white/10' },
                    { label: 'Completed', value: completedTasks, color: 'text-green-400', bgColor: 'bg-green-500/5 border-green-500/10' },
                    { label: 'In Progress', value: inProgressTasks, color: 'text-blue-400', bgColor: 'bg-blue-500/5 border-blue-500/10' },
                    { label: 'Urgent', value: urgentTasks, color: 'text-red-400', bgColor: 'bg-red-500/5 border-red-500/10' },
                ].map(stat => (
                    <div key={stat.label} className={`p-4 rounded-2xl border ${stat.bgColor} transition-all`}>
                        <div className={`text-2xl font-bold font-display ${stat.color}`}>{stat.value}</div>
                        <div className="text-xs text-white/40 mt-1">{stat.label}</div>
                    </div>
                ))}
            </div>

            {/* Priority Matrix */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-6 rounded-3xl glass-card bg-purple-500/5 border-purple-500/10">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold text-white mb-2">Focus Timer</h3>
                        <div className="flex gap-2">
                             <select
                                value={focusDuration / 60}
                                onChange={handleDurationChange}
                                disabled={timerActive}
                                className="bg-white/5 border border-white/10 text-white/70 text-sm rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-purple-500"
                             >
                                <option value={15} className="bg-slate-900">15 min</option>
                                <option value={25} className="bg-slate-900">25 min</option>
                                <option value={50} className="bg-slate-900">50 min</option>
                             </select>
                            <Clock className="text-purple-400" />
                        </div>
                    </div>
                    <div className="text-center py-6">
                        <div className="text-6xl font-bold text-white font-display text-glow mb-4">
                            {formatTime(focusTime)}
                        </div>
                        <p className="text-white/40 mb-6">
                            {timerActive ? 'Focusing...' : focusTime > 0 ? 'Ready to focus?' : 'Session Complete!'}
                        </p>
                        
                        <div className="flex items-center justify-center gap-4">
                            <button
                                onClick={toggleTimer}
                                className={`flex items-center gap-2 px-8 py-3 rounded-full font-medium transition-colors ${
                                    timerActive
                                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30'
                                    : 'bg-purple-600 hover:bg-purple-700 text-white shadow-lg shadow-purple-500/25'
                                }`}
                            >
                                {timerActive ? (
                                    <><Pause size={18} /> Pause</>
                                ) : (
                                    <><Play size={18} /> Start</>
                                )}
                            </button>
                            
                            <button 
                                onClick={resetTimer}
                                className="p-3 bg-white/5 hover:bg-white/10 text-white/60 hover:text-white rounded-full transition-colors border border-white/10"
                                title="Reset Timer"
                            >
                                <RotateCcw size={18} />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="p-6 rounded-3xl glass-card bg-purple-500/5 border-purple-500/10">
                    <h3 className="text-xl font-bold text-white mb-6">Priority Breakdown</h3>
                    <div className="space-y-3">
                        {['urgent', 'high', 'medium', 'low'].map(p => {
                            const count = allTasks.filter(t => t.priority === p && t.status !== 'completed').length;
                            const pct = totalTasks > 0 ? (count / totalTasks) * 100 : 0;
                            return (
                                <div key={p} className="flex items-center gap-3">
                                    <div className={`w-3 h-3 rounded-full ${priorityDot[p]}`} />
                                    <span className="text-sm text-white/60 capitalize w-16">{p}</span>
                                    <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${pct}%` }}
                                            className={`h-full rounded-full ${priorityDot[p]}`}
                                            transition={{ duration: 0.6 }}
                                        />
                                    </div>
                                    <span className="text-sm text-white/40 w-8 text-right">{count}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Task List */}
            <div className="rounded-3xl bg-black/20 backdrop-blur-sm border border-white/10 overflow-hidden shadow-xl">
                <div className="flex border-b border-white/10">
                    {filterTabs.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setFilter(tab.key)}
                            className={`flex-1 py-4 text-center font-medium transition-colors relative ${filter === tab.key ? 'text-purple-400 bg-white/5' : 'text-white/40 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            {tab.label}
                            {filter === tab.key && (
                                <motion.div
                                    layoutId="activeTab"
                                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400"
                                />
                            )}
                        </button>
                    ))}
                </div>

                <div className="divide-y divide-white/10">
                    {loading ? (
                        <div className="p-8 text-center text-white/40 flex items-center justify-center gap-2">
                            <Loader2 size={20} className="animate-spin" />
                            Loading tasks...
                        </div>
                    ) : tasks.length === 0 ? (
                        <div className="p-12 text-center">
                            <CheckCircle size={40} className="text-white/10 mx-auto mb-3" />
                            <p className="text-white/40">No tasks in this category.</p>
                            <p className="text-white/20 text-sm mt-1">Use the Orchestrator to generate tasks, or add one manually.</p>
                        </div>
                    ) : (
                        <AnimatePresence>
                            {tasks.map((task) => (
                                <motion.div
                                    key={task.id}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0, x: -50 }}
                                    className="p-4 flex items-start gap-4 hover:bg-white/5 transition-colors group"
                                >
                                    <button
                                        onClick={() => handleToggleStatus(task)}
                                        className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all mt-0.5 ${task.status === 'completed'
                                            ? 'bg-purple-500 border-purple-500 text-white'
                                            : 'border-white/20 text-transparent hover:border-purple-500'
                                            }`}
                                    >
                                        <CheckCircle size={14} fill="currentColor" />
                                    </button>

                                    <div
                                        className="flex-1 min-w-0 cursor-pointer"
                                        onClick={() => setExpandedTask(expandedTask === task.id ? null : task.id)}
                                    >
                                        <h4 className={`text-white font-medium ${task.status === 'completed' ? 'line-through text-white/40' : ''}`}>
                                            {task.title}
                                        </h4>
                                        {task.description && (
                                            <p className={`text-sm text-white/40 mt-0.5 ${expandedTask === task.id ? '' : 'truncate'}`}>
                                                {task.description}
                                            </p>
                                        )}
                                        {task.due_date && (
                                            <div className="flex items-center gap-1 mt-1 text-xs text-white/30">
                                                <Clock size={12} />
                                                Due {new Date(task.due_date).toLocaleDateString()}
                                            </div>
                                        )}
                                    </div>

                                    <div className={`px-3 py-1 rounded-full text-xs font-medium border ${priorityColors[task.priority] || priorityColors.medium}`}>
                                        {task.priority}
                                    </div>

                                    <button
                                        onClick={() => handleDeleteTask(task.id)}
                                        className="opacity-0 group-hover:opacity-100 text-white/20 hover:text-red-400 transition-all p-1"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    )}
                </div>
            </div>

            {/* Add Task Modal */}
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
                                <h3 className="text-xl font-bold text-white">New Task</h3>
                                <button onClick={() => setShowAddModal(false)} className="text-white/40 hover:text-white">
                                    <X size={20} />
                                </button>
                            </div>
                            <form onSubmit={handleAddTask} className="space-y-4">
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Title</label>
                                    <input
                                        type="text"
                                        value={addForm.title}
                                        onChange={e => setAddForm(p => ({ ...p, title: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3"
                                        placeholder="What needs to be done?"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Description</label>
                                    <textarea
                                        value={addForm.description}
                                        onChange={e => setAddForm(p => ({ ...p, description: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3 resize-none"
                                        rows={3}
                                        placeholder="Additional details..."
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Priority</label>
                                    <div className="flex gap-2">
                                        {['low', 'medium', 'high', 'urgent'].map(p => (
                                            <button
                                                key={p}
                                                type="button"
                                                onClick={() => setAddForm(prev => ({ ...prev, priority: p }))}
                                                className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all capitalize ${addForm.priority === p
                                                    ? priorityColors[p] + ' ring-1 ring-white/20'
                                                    : 'bg-white/5 border-white/10 text-white/40'
                                                    }`}
                                            >
                                                {p}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <button
                                    type="submit"
                                    disabled={adding}
                                    className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {adding ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
                                    {adding ? 'Creating...' : 'Create Task'}
                                </button>
                            </form>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default Productivity;
