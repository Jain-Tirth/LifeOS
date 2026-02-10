import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Utensils, ShoppingCart, RefreshCw, ChevronDown, Plus } from 'lucide-react';
import { getMealPlans } from '../../api/meals';

const MealPlanner = () => {
    const [meals, setMeals] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchMeals();
    }, []);

    const fetchMeals = async () => {
        try {
            const res = await getMealPlans();
            // Handle pagination or direct array
            const data = res.data.results || res.data;
            setMeals(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const mealTypes = ['Breakfast', 'Lunch', 'Dinner'];

    return (
         <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
             <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Meal Planner</h2>
                    <p className="text-white/60">Plan your week, eat healthy.</p>
                </div>
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-colors border border-white/10">
                        <ShoppingCart size={20} />
                        <span>Auto-Grocery</span>
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl transition-colors">
                        <Plus size={20} />
                        <span>Add Meal</span>
                    </button>
                </div>
            </header>

            {/* Weekly Menu Grid */}
            <div className="rounded-3xl glass-card overflow-hidden">
                <div className="grid grid-cols-4 divide-x divide-white/10 border-b border-white/10 bg-white/5 text-white/70 font-medium">
                    <div className="p-4">Day</div>
                    {mealTypes.map(t => <div key={t} className="p-4">{t}</div>)}
                </div>
                <div className="divide-y divide-white/10">
                    {days.map((day) => (
                        <div key={day} className="grid grid-cols-4 divide-x divide-white/10 hover:bg-white/5 transition-colors group">
                            <div className="p-4 text-white font-medium">{day}</div>
                            {mealTypes.map(type => (
                                <div key={type} className="p-4 relative">
                                    <div className="text-sm text-white/50 italic group-hover:text-white/20">Empty</div>
                                    <button className="absolute inset-0 w-full h-full opacity-0 hover:opacity-100 flex items-center justify-center bg-black/20 text-white backdrop-blur-sm transition-opacity">
                                        <Plus size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    ))}
                </div>
            </div>

            {/* Recipe Cards Mock */}
            <h3 className="text-xl font-bold text-white">Suggested Recipes</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="group p-4 rounded-3xl glass-card bg-green-500/5 border-green-500/10 hover:border-green-500/30 transition-all cursor-pointer">
                        <div className="h-40 w-full bg-black/20 rounded-2xl mb-4 overflow-hidden relative">
                             {/* Placeholder Image */}
                             <div className="absolute inset-0 flex items-center justify-center text-white/20">
                                <Utensils size={40} />
                             </div>
                             <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-md text-white text-xs px-2 py-1 rounded-full">
                                450 kcal
                             </div>
                        </div>
                        <h4 className="text-lg font-bold text-white mb-2">Quinoa & Avocado Salad</h4>
                        <div className="flex justify-between items-center text-sm text-white/40">
                            <span>15 mins prep</span>
                            <span className="flex items-center gap-1 group-hover:text-green-400 transition-colors">
                                View Recipe <ChevronDown size={14} className="-rotate-90" />
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
};

export default MealPlanner;
