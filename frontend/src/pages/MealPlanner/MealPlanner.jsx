import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Utensils, RefreshCw, Plus, Trash2, Clock, X, Loader2,
    ChevronDown, ChevronUp, Flame, ShoppingCart, Check, Timer, BookOpen
} from 'lucide-react';
import { getMealPlans, createMealPlan, deleteMealPlan } from '../../api/meals';
import { useToast } from '../../context/ToastContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MealPlanner = () => {
    const [meals, setMeals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [expandedMeal, setExpandedMeal] = useState(null);
    const [checkedIngredients, setCheckedIngredients] = useState({});
    const [addForm, setAddForm] = useState({
        meal_name: '',
        meal_type: 'dinner',
        date: new Date().toISOString().split('T')[0],
        instructions: '',
    });
    const [adding, setAdding] = useState(false);
    const [activeView, setActiveView] = useState('cards'); // 'cards' or 'weekly'
    const toast = useToast();

    useEffect(() => {
        fetchMeals();
    }, []);

    const fetchMeals = async () => {
        setLoading(true);
        try {
            const res = await getMealPlans();
            const data = res.data.results || res.data;
            setMeals(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteMeal = async (id) => {
        try {
            await deleteMealPlan(id);
            toast.success('Meal removed');
            fetchMeals();
        } catch (error) {
            console.error(error);
            toast.error('Failed to delete meal.');
        }
    };

    const handleAddMeal = async (e) => {
        e.preventDefault();
        if (!addForm.meal_name.trim()) return;
        setAdding(true);
        try {
            await createMealPlan(addForm);
            toast.success('Meal added successfully!');
            setShowAddModal(false);
            setAddForm({ meal_name: '', meal_type: 'dinner', date: new Date().toISOString().split('T')[0], instructions: '' });
            fetchMeals();
        } catch (error) {
            console.error(error);
            toast.error('Failed to add meal.');
        } finally {
            setAdding(false);
        }
    };

    const toggleIngredient = (mealId, index) => {
        setCheckedIngredients(prev => {
            const key = `${mealId}-${index}`;
            return { ...prev, [key]: !prev[key] };
        });
    };

    // Build weekly view data
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const mealTypes = ['breakfast', 'lunch', 'dinner'];
    const mealTypeLabels = { breakfast: 'Breakfast', lunch: 'Lunch', dinner: 'Dinner', snack: 'Snack' };
    const mealTypeEmoji = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '🍪' };

    const getWeekDates = () => {
        const now = new Date();
        const dayOfWeek = now.getDay();
        const monday = new Date(now);
        monday.setDate(now.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
        return days.map((_, i) => {
            const d = new Date(monday);
            d.setDate(monday.getDate() + i);
            return d.toISOString().split('T')[0];
        });
    };

    const weekDates = getWeekDates();
    const mealIndex = {};
    meals.forEach(meal => {
        const key = `${meal.date}_${meal.meal_type}`;
        if (!mealIndex[key]) mealIndex[key] = [];
        mealIndex[key].push(meal);
    });

    const mealTypeColors = {
        breakfast: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', accent: 'from-amber-500/20 to-amber-600/5' },
        lunch: { bg: 'bg-sky-500/10', text: 'text-sky-400', border: 'border-sky-500/20', accent: 'from-sky-500/20 to-sky-600/5' },
        dinner: { bg: 'bg-violet-500/10', text: 'text-violet-400', border: 'border-violet-500/20', accent: 'from-violet-500/20 to-violet-600/5' },
        snack: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', accent: 'from-emerald-500/20 to-emerald-600/5' },
    };

    // ─── Recipe Card Component ────────────────────────────────────────────
    const RecipeCard = ({ meal }) => {
        const isExpanded = expandedMeal === meal.id;
        const colors = mealTypeColors[meal.meal_type] || mealTypeColors.dinner;
        const hasIngredients = meal.ingredients && Array.isArray(meal.ingredients) && meal.ingredients.length > 0;
        const hasInstructions = meal.instructions && meal.instructions.length > 0;
        const hasNutrition = meal.nutritional_info && typeof meal.nutritional_info === 'object';
        const hasTimes = meal.preferences?.times;

        return (
            <motion.div
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`rounded-3xl glass-card overflow-hidden transition-all duration-300 group hover:border-green-500/20 ${isExpanded ? 'ring-1 ring-green-500/20' : ''}`}
            >
                {/* Card Header — always visible */}
                <div
                    className={`p-5 cursor-pointer bg-gradient-to-br ${colors.accent}`}
                    onClick={() => setExpandedMeal(isExpanded ? null : meal.id)}
                >
                    <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                                <span className={`text-xs px-2.5 py-1 rounded-full ${colors.bg} ${colors.text} ${colors.border} border font-medium`}>
                                    {mealTypeEmoji[meal.meal_type]} {mealTypeLabels[meal.meal_type] || meal.meal_type}
                                </span>
                                <span className="text-xs text-white/30">
                                    {new Date(meal.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                                </span>
                            </div>
                            <h3 className="text-lg font-bold text-white group-hover:text-green-300 transition-colors">{meal.meal_name}</h3>
                            {/* Quick info badges */}
                            <div className="flex items-center gap-3 mt-2 flex-wrap">
                                {hasIngredients && (
                                    <span className="flex items-center gap-1 text-xs text-white/40">
                                        <ShoppingCart size={12} /> {meal.ingredients.length} ingredients
                                    </span>
                                )}
                                {hasTimes && (
                                    <>
                                        {meal.preferences.times.prep && (
                                            <span className="flex items-center gap-1 text-xs text-white/40">
                                                <Timer size={12} /> Prep: {meal.preferences.times.prep}
                                            </span>
                                        )}
                                        {meal.preferences.times.cook && (
                                            <span className="flex items-center gap-1 text-xs text-white/40">
                                                <Flame size={12} /> Cook: {meal.preferences.times.cook}
                                            </span>
                                        )}
                                    </>
                                )}
                                {hasNutrition && meal.nutritional_info.calories && (
                                    <span className="flex items-center gap-1 text-xs text-white/40">
                                        <Flame size={12} /> {meal.nutritional_info.calories} cal
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className="flex items-center gap-2 ml-3">
                            <button
                                onClick={(e) => { e.stopPropagation(); handleDeleteMeal(meal.id); }}
                                className="opacity-0 group-hover:opacity-100 p-1.5 text-white/20 hover:text-red-400 transition-all"
                            >
                                <Trash2 size={14} />
                            </button>
                            <div className={`p-1 rounded-full transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                                <ChevronDown size={18} className="text-white/40" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Expanded Content */}
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="overflow-hidden"
                        >
                            <div className="p-5 pt-0 space-y-5">
                                {/* Nutritional Info Bar */}
                                {hasNutrition && (
                                    <div className="flex flex-wrap gap-3 pt-4 mt-1 border-t border-white/5">
                                        {Object.entries(meal.nutritional_info).map(([key, value]) => (
                                            <div key={key} className="flex flex-col items-center px-4 py-2 rounded-xl bg-white/5 border border-white/5 min-w-[70px]">
                                                <span className="text-sm font-bold text-white">{value}</span>
                                                <span className="text-[10px] text-white/40 uppercase tracking-wider">{key}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Ingredients Checklist */}
                                {hasIngredients && (
                                    <div className="pt-4 border-t border-white/5">
                                        <div className="flex items-center justify-between mb-3">
                                            <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                                <ShoppingCart size={14} className="text-green-400" />
                                                Ingredients
                                            </h4>
                                            <span className="text-xs text-white/30">
                                                {meal.ingredients.filter((_, i) => checkedIngredients[`${meal.id}-${i}`]).length}/{meal.ingredients.length} checked
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                                            {meal.ingredients.map((ingredient, i) => {
                                                const isChecked = checkedIngredients[`${meal.id}-${i}`];
                                                return (
                                                    <button
                                                        key={i}
                                                        onClick={() => toggleIngredient(meal.id, i)}
                                                        className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-all text-sm ${isChecked
                                                            ? 'bg-green-500/10 text-white/40 line-through'
                                                            : 'bg-white/5 text-white/80 hover:bg-white/10'
                                                            }`}
                                                    >
                                                        <div className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 border transition-colors ${isChecked
                                                            ? 'bg-green-500 border-green-500'
                                                            : 'border-white/20'
                                                            }`}>
                                                            {isChecked && <Check size={10} className="text-white" />}
                                                        </div>
                                                        <span>{ingredient}</span>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}

                                {/* Instructions */}
                                {hasInstructions && (
                                    <div className="pt-4 border-t border-white/5">
                                        <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                                            <BookOpen size={14} className="text-blue-400" />
                                            Instructions
                                        </h4>
                                        <div className="prose prose-invert prose-sm max-w-none text-white/70 leading-relaxed">
                                            <ReactMarkdown
                                                remarkPlugins={[remarkGfm]}
                                                components={{
                                                    p: ({ children }) => <p className="text-white/70 mb-2">{children}</p>,
                                                    ol: ({ children }) => <ol className="list-decimal list-inside space-y-2 mb-3">{children}</ol>,
                                                    ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-3">{children}</ul>,
                                                    li: ({ children }) => (
                                                        <li className="text-white/70 pl-1">
                                                            <span className="text-white/70">{children}</span>
                                                        </li>
                                                    ),
                                                    strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                                                    h1: ({ children }) => <h3 className="text-lg font-bold text-white mt-3 mb-2">{children}</h3>,
                                                    h2: ({ children }) => <h4 className="text-base font-bold text-white mt-3 mb-2">{children}</h4>,
                                                    h3: ({ children }) => <h5 className="text-sm font-bold text-white mt-2 mb-1">{children}</h5>,
                                                }}
                                            >
                                                {meal.instructions}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                )}

                                {/* Tips */}
                                {meal.preferences?.tips && (
                                    <div className="pt-4 border-t border-white/5">
                                        <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
                                            💡 Tips
                                        </h4>
                                        <p className="text-sm text-white/50">{meal.preferences.tips}</p>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        );
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
            <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Meal Planner</h2>
                    <p className="text-white/60">
                        {meals.length > 0
                            ? `${meals.length} recipe${meals.length === 1 ? '' : 's'} saved`
                            : 'Plan your week, eat healthy.'}
                    </p>
                </div>
                <div className="flex gap-3">
                    {/* View Toggle */}
                    <div className="flex bg-white/5 rounded-xl p-0.5 border border-white/10">
                        <button
                            onClick={() => setActiveView('cards')}
                            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${activeView === 'cards' ? 'bg-white/10 text-white' : 'text-white/40'}`}
                        >
                            Recipes
                        </button>
                        <button
                            onClick={() => setActiveView('weekly')}
                            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${activeView === 'weekly' ? 'bg-white/10 text-white' : 'text-white/40'}`}
                        >
                            Weekly
                        </button>
                    </div>
                    <button
                        onClick={fetchMeals}
                        className="p-2.5 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white rounded-xl transition-colors border border-white/10"
                    >
                        <RefreshCw size={18} />
                    </button>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl transition-colors"
                    >
                        <Plus size={20} />
                        <span>Add Meal</span>
                    </button>
                </div>
            </header>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 size={32} className="animate-spin text-white/30" />
                </div>
            ) : meals.length === 0 ? (
                <div className="text-center py-20">
                    <div className="relative inline-block mb-6">
                        <div className="absolute inset-0 bg-green-500/20 rounded-full blur-2xl scale-150" />
                        <Utensils size={56} className="text-white/15 relative" />
                    </div>
                    <p className="text-white/40 text-lg mb-2">No recipes saved yet</p>
                    <p className="text-white/20 text-sm mb-6">Ask the Orchestrator to plan your meals, then save them here.</p>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl transition-colors inline-flex items-center gap-2"
                    >
                        <Plus size={18} />
                        Add Your First Meal
                    </button>
                </div>
            ) : (
                <>
                    {/* ─── Cards View ──────────────────────────────────────── */}
                    {activeView === 'cards' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {meals.map((meal) => (
                                <RecipeCard key={meal.id} meal={meal} />
                            ))}
                        </div>
                    )}

                    {/* ─── Weekly View ─────────────────────────────────────── */}
                    {activeView === 'weekly' && (
                        <div className="rounded-3xl glass-card overflow-hidden">
                            <div className="grid grid-cols-4 divide-x divide-white/10 border-b border-white/10 bg-white/5">
                                <div className="p-4 text-white/50 font-medium text-sm">Day</div>
                                {mealTypes.map(t => (
                                    <div key={t} className="p-4 text-white/50 font-medium text-sm">
                                        {mealTypeEmoji[t]} {mealTypeLabels[t]}
                                    </div>
                                ))}
                            </div>
                            <div className="divide-y divide-white/10">
                                {days.map((day, dayIdx) => {
                                    const dateStr = weekDates[dayIdx];
                                    const isToday = dateStr === new Date().toISOString().split('T')[0];
                                    return (
                                        <div key={day} className={`grid grid-cols-4 divide-x divide-white/10 group ${isToday ? 'bg-green-500/5' : 'hover:bg-white/[0.02]'}`}>
                                            <div className="p-4">
                                                <div className={`font-medium text-sm ${isToday ? 'text-green-400' : 'text-white'}`}>{day}</div>
                                                <div className="text-xs text-white/25 mt-0.5">
                                                    {new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                                </div>
                                            </div>
                                            {mealTypes.map(type => {
                                                const key = `${dateStr}_${type}`;
                                                const cellMeals = mealIndex[key] || [];
                                                return (
                                                    <div key={type} className="p-3 relative min-h-[65px]">
                                                        {cellMeals.length > 0 ? (
                                                            <div className="space-y-1">
                                                                {cellMeals.map(m => (
                                                                    <div
                                                                        key={m.id}
                                                                        className={`text-xs font-medium p-2 rounded-lg ${mealTypeColors[type].bg} ${mealTypeColors[type].text} ${mealTypeColors[type].border} border truncate cursor-pointer hover:brightness-110`}
                                                                        onClick={() => { setActiveView('cards'); setExpandedMeal(m.id); }}
                                                                    >
                                                                        {m.meal_name}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        ) : (
                                                            <div className="text-xs text-white/15 italic">—</div>
                                                        )}
                                                        <button
                                                            onClick={() => {
                                                                setAddForm(prev => ({ ...prev, date: dateStr, meal_type: type }));
                                                                setShowAddModal(true);
                                                            }}
                                                            className="absolute inset-0 w-full h-full opacity-0 hover:opacity-100 flex items-center justify-center bg-black/40 backdrop-blur-sm text-white/70 transition-opacity"
                                                        >
                                                            <Plus size={16} />
                                                        </button>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* ─── Add Meal Modal ──────────────────────────────────────────── */}
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
                                <h3 className="text-xl font-bold text-white">Add Meal</h3>
                                <button onClick={() => setShowAddModal(false)} className="text-white/40 hover:text-white">
                                    <X size={20} />
                                </button>
                            </div>
                            <form onSubmit={handleAddMeal} className="space-y-4">
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Meal Name</label>
                                    <input
                                        type="text"
                                        value={addForm.meal_name}
                                        onChange={e => setAddForm(p => ({ ...p, meal_name: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3"
                                        placeholder="e.g., Grilled Salmon with Asparagus"
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm text-white/60 mb-1 block">Type</label>
                                        <select
                                            value={addForm.meal_type}
                                            onChange={e => setAddForm(p => ({ ...p, meal_type: e.target.value }))}
                                            className="w-full glass-input rounded-xl px-4 py-3"
                                        >
                                            <option value="breakfast">🌅 Breakfast</option>
                                            <option value="lunch">☀️ Lunch</option>
                                            <option value="dinner">🌙 Dinner</option>
                                            <option value="snack">🍪 Snack</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-sm text-white/60 mb-1 block">Date</label>
                                        <input
                                            type="date"
                                            value={addForm.date}
                                            onChange={e => setAddForm(p => ({ ...p, date: e.target.value }))}
                                            className="w-full glass-input rounded-xl px-4 py-3"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm text-white/60 mb-1 block">Instructions (optional)</label>
                                    <textarea
                                        value={addForm.instructions}
                                        onChange={e => setAddForm(p => ({ ...p, instructions: e.target.value }))}
                                        className="w-full glass-input rounded-xl px-4 py-3 resize-none"
                                        rows={3}
                                        placeholder="How to prepare..."
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={adding}
                                    className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {adding ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
                                    {adding ? 'Adding...' : 'Add Meal'}
                                </button>
                            </form>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default MealPlanner;
