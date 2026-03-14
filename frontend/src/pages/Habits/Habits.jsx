import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Flame, Plus, X, Loader2, Target, TrendingUp,
  CheckCircle, Circle, Trophy, Zap, Sparkles,
  Heart, Brain, BookOpen, Users, Wallet, Star
} from 'lucide-react';
import { getHabits, createHabit, toggleHabitToday, deleteHabit } from '../../api/habits';
import { useToast } from '../../context/ToastContext';

const CATEGORY_META = {
  health:       { icon: Heart,    color: '#EF4444', label: 'Health' },
  productivity: { icon: Target,   color: '#8B5CF6', label: 'Productivity' },
  mindfulness:  { icon: Sparkles, color: '#06B6D4', label: 'Mindfulness' },
  learning:     { icon: BookOpen, color: '#F59E0B', label: 'Learning' },
  social:       { icon: Users,    color: '#10B981', label: 'Social' },
  self_care:    { icon: Star,     color: '#EC4899', label: 'Self Care' },
  finance:      { icon: Wallet,   color: '#14B8A6', label: 'Finance' },
  other:        { icon: Zap,      color: '#6366F1', label: 'Other' },
};

const FREQUENCY_OPTIONS = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekdays', label: 'Weekdays' },
  { value: 'weekends', label: 'Weekends' },
  { value: 'weekly', label: 'Weekly' },
];

const ICON_OPTIONS = ['✅', '🏋️', '📖', '🧘', '💧', '🏃', '💤', '🥗', '💰', '🎯', '🧠', '❤️'];

const Habits = () => {
  const [habits, setHabits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState({});
  const [showAddModal, setShowAddModal] = useState(false);
  const [adding, setAdding] = useState(false);
  const [addForm, setAddForm] = useState({
    name: '', description: '', category: 'health',
    frequency: 'daily', icon: '✅', color: '#8B5CF6', target_count: 1,
  });
  const toast = useToast();

  const fetchHabits = useCallback(async () => {
    try {
      const res = await getHabits();
      const data = res.data.results || res.data;
      setHabits(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load habits');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { fetchHabits(); }, [fetchHabits]);

  const handleToggle = async (habitId) => {
    setToggling(prev => ({ ...prev, [habitId]: true }));
    try {
      const res = await toggleHabitToday(habitId);
      const data = res.data;
      setHabits(prev => prev.map(h =>
        h.id === habitId ? {
          ...h,
          completed_today: data.completed,
          current_streak: data.current_streak,
          best_streak: data.best_streak,
          total_completions: data.total_completions,
        } : h
      ));
      toast.success(data.completed ? '🔥 Habit completed!' : 'Habit unchecked');
    } catch (err) {
      console.error(err);
      toast.error('Failed to toggle habit');
    } finally {
      setToggling(prev => ({ ...prev, [habitId]: false }));
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!addForm.name.trim()) return;
    setAdding(true);
    try {
      await createHabit(addForm);
      toast.success('Habit created! 🎯');
      setShowAddModal(false);
      setAddForm({ name: '', description: '', category: 'health', frequency: 'daily', icon: '✅', color: '#8B5CF6', target_count: 1 });
      fetchHabits();
    } catch (err) {
      console.error(err);
      toast.error('Failed to create habit');
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteHabit(id);
      toast.success('Habit removed');
      fetchHabits();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  // Stats
  const totalHabits = habits.length;
  const completedToday = habits.filter(h => h.completed_today).length;
  const longestStreak = habits.reduce((max, h) => Math.max(max, h.best_streak || 0), 0);
  const totalCompletions = habits.reduce((sum, h) => sum + (h.total_completions || 0), 0);
  const completionPct = totalHabits > 0 ? Math.round((completedToday / totalHabits) * 100) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8 scroll-gpu"
    >
      {/* Header */}
      <header className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-white mb-1 font-display">Habits</h2>
          <p className="text-white/60">
            {totalHabits > 0
              ? `${completedToday}/${totalHabits} done today · ${completionPct}%`
              : 'Build habits that stick.'}
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl transition-colors"
        >
          <Plus size={20} />
          <span>New Habit</span>
        </button>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Today', value: `${completedToday}/${totalHabits}`, icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/5 border-green-500/10' },
          { label: 'Completion', value: `${completionPct}%`, icon: Target, color: 'text-purple-400', bg: 'bg-purple-500/5 border-purple-500/10' },
          { label: 'Best Streak', value: `${longestStreak}d`, icon: Flame, color: 'text-orange-400', bg: 'bg-orange-500/5 border-orange-500/10' },
          { label: 'All-time', value: totalCompletions, icon: TrendingUp, color: 'text-blue-400', bg: 'bg-blue-500/5 border-blue-500/10' },
        ].map(stat => (
          <div key={stat.label} className={`p-4 rounded-2xl border ${stat.bg} transition-all`}>
            <div className="flex items-center gap-2 mb-2">
              <stat.icon size={16} className={`${stat.color}`} />
              <span className="text-xs text-white/40">{stat.label}</span>
            </div>
            <div className={`text-2xl font-bold font-display ${stat.color}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Progress Ring */}
      {totalHabits > 0 && (
        <div className="flex items-center justify-center py-4">
          <div className="relative w-32 h-32">
            <svg className="w-32 h-32 -rotate-90" viewBox="0 0 128 128">
              <circle cx="64" cy="64" r="56" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
              <circle
                cx="64" cy="64" r="56" fill="none"
                stroke="#8B5CF6" strokeWidth="8" strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 56}`}
                strokeDashoffset={`${2 * Math.PI * 56 * (1 - completionPct / 100)}`}
                className="transition-all duration-700 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-white font-display">{completionPct}%</span>
              <span className="text-xs text-white/40">today</span>
            </div>
          </div>
        </div>
      )}

      {/* Habit Cards */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-8 text-center text-white/40 flex items-center justify-center gap-2">
            <Loader2 size={20} className="animate-spin" />
            Loading habits...
          </div>
        ) : habits.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-black/20 border border-white/10">
            <Flame size={48} className="text-white/10 mx-auto mb-3" />
            <p className="text-white/40 text-lg">No habits yet</p>
            <p className="text-white/20 text-sm mt-1">Start small. Build one habit at a time.</p>
          </div>
        ) : (
          <AnimatePresence>
            {habits.map((habit) => {
              const cat = CATEGORY_META[habit.category] || CATEGORY_META.other;
              const CatIcon = cat.icon;
              const isCompleted = habit.completed_today;
              const isTogglingThis = toggling[habit.id];

              return (
                <motion.div
                  key={habit.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -40 }}
                  className={`group relative p-4 rounded-2xl border backdrop-blur-sm transition-all duration-300 ${
                    isCompleted
                      ? 'bg-green-500/5 border-green-500/20'
                      : 'bg-white/[0.02] border-white/10 hover:bg-white/[0.04]'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    {/* Toggle Button */}
                    <button
                      onClick={() => handleToggle(habit.id)}
                      disabled={isTogglingThis}
                      className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-lg transition-all duration-300 ${
                        isCompleted
                          ? 'bg-green-500/20 ring-2 ring-green-500/40 scale-110'
                          : 'bg-white/5 hover:bg-white/10 ring-1 ring-white/10'
                      }`}
                    >
                      {isTogglingThis ? (
                        <Loader2 size={16} className="animate-spin text-white/40" />
                      ) : isCompleted ? (
                        <span className="animate-bounce-once">✓</span>
                      ) : (
                        <span className="opacity-70">{habit.icon}</span>
                      )}
                    </button>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className={`font-medium ${isCompleted ? 'text-green-300 line-through' : 'text-white'}`}>
                          {habit.name}
                        </h4>
                        <span
                          className="px-2 py-0.5 rounded-full text-[10px] font-medium border"
                          style={{
                            color: cat.color,
                            borderColor: `${cat.color}33`,
                            backgroundColor: `${cat.color}11`,
                          }}
                        >
                          {cat.label}
                        </span>
                      </div>
                      {habit.description && (
                        <p className="text-sm text-white/40 mt-0.5 truncate">{habit.description}</p>
                      )}
                    </div>

                    {/* Streak */}
                    <div className="flex items-center gap-3">
                      {habit.current_streak > 0 && (
                        <div className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-orange-500/10 border border-orange-500/20">
                          <Flame size={14} className="text-orange-400" />
                          <span className="text-sm font-bold text-orange-300">{habit.current_streak}</span>
                        </div>
                      )}

                      {/* Best Streak Badge */}
                      {habit.best_streak >= 7 && (
                        <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                          <Trophy size={12} className="text-yellow-400" />
                          <span className="text-xs text-yellow-300">{habit.best_streak}</span>
                        </div>
                      )}

                      {/* Delete */}
                      <button
                        onClick={() => handleDelete(habit.id)}
                        className="opacity-0 group-hover:opacity-100 text-white/20 hover:text-red-400 transition-all p-1"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>

      {/* Add Habit Modal */}
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
                <h3 className="text-xl font-bold text-white">New Habit</h3>
                <button onClick={() => setShowAddModal(false)} className="text-white/40 hover:text-white">
                  <X size={20} />
                </button>
              </div>
              <form onSubmit={handleCreate} className="space-y-4">
                {/* Name */}
                <div>
                  <label className="text-sm text-white/60 mb-1 block">Habit Name</label>
                  <input
                    type="text"
                    value={addForm.name}
                    onChange={e => setAddForm(p => ({ ...p, name: e.target.value }))}
                    className="w-full glass-input rounded-xl px-4 py-3"
                    placeholder="e.g., Morning Walk"
                    required
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="text-sm text-white/60 mb-1 block">Description (optional)</label>
                  <input
                    type="text"
                    value={addForm.description}
                    onChange={e => setAddForm(p => ({ ...p, description: e.target.value }))}
                    className="w-full glass-input rounded-xl px-4 py-3"
                    placeholder="Walk 10 minutes after waking up"
                  />
                </div>

                {/* Icon Picker */}
                <div>
                  <label className="text-sm text-white/60 mb-1 block">Icon</label>
                  <div className="flex flex-wrap gap-2">
                    {ICON_OPTIONS.map(icon => (
                      <button
                        key={icon}
                        type="button"
                        onClick={() => setAddForm(p => ({ ...p, icon }))}
                        className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg border transition-all ${
                          addForm.icon === icon
                            ? 'bg-purple-500/20 border-purple-500/40 ring-1 ring-purple-400/30'
                            : 'bg-white/5 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {icon}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Category */}
                <div>
                  <label className="text-sm text-white/60 mb-1 block">Category</label>
                  <div className="grid grid-cols-4 gap-2">
                    {Object.entries(CATEGORY_META).map(([key, meta]) => {
                      const Icon = meta.icon;
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() => setAddForm(p => ({ ...p, category: key, color: meta.color }))}
                          className={`flex flex-col items-center gap-1 p-2 rounded-xl border text-xs transition-all ${
                            addForm.category === key
                              ? 'border-white/20 bg-white/10'
                              : 'border-white/5 bg-white/[0.02] hover:bg-white/5'
                          }`}
                        >
                          <Icon size={16} style={{ color: meta.color }} />
                          <span className="text-white/60">{meta.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Frequency */}
                <div>
                  <label className="text-sm text-white/60 mb-1 block">Frequency</label>
                  <div className="flex gap-2">
                    {FREQUENCY_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setAddForm(p => ({ ...p, frequency: opt.value }))}
                        className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all ${
                          addForm.frequency === opt.value
                            ? 'bg-purple-500/20 border-purple-500/30 text-purple-300'
                            : 'bg-white/5 border-white/10 text-white/40 hover:bg-white/10'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={adding}
                  className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {adding ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
                  {adding ? 'Creating...' : 'Create Habit'}
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default Habits;
