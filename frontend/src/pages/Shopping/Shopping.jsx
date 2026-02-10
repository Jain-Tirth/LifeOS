import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, Plus, CreditCard } from 'lucide-react';

import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip, Cell } from 'recharts';

const Shopping = () => {
    // Mock Data
    const [items, setItems] = useState([
        { id: 1, name: 'Almond Milk', category: 'Groceries', price: 4.50, status: 'pending' },
        { id: 2, name: 'Wireless Mouse', category: 'Tech', price: 29.99, status: 'bought' },
        { id: 3, name: 'Yoga Mat', category: 'Wellness', price: 25.00, status: 'pending' },
        { id: 4, name: 'Coffee Beans', category: 'Groceries', price: 18.00, status: 'pending' },
    ]);

    const spendingData = [
        { category: 'Groceries', amount: 150 },
        { category: 'Tech', amount: 300 },
        { category: 'Clothes', amount: 120 },
        { category: 'Home', amount: 80 },
    ];
    
    // Custom Bar Shape for sleek look
    const CustomBar = (props) => {
        const { fill, x, y, width, height } = props;
        return <rect x={x} y={y} width={width} height={height} rx={6} fill={fill} fillOpacity={0.8} />;
    };

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
             <header className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-1 font-display">Shopping</h2>
                    <p className="text-white/60">Manage your wishlist and expenses.</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl transition-colors">
                    <Plus size={20} />
                    <span>Add Item</span>
                </button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Total Budget Card */}
                <div className="p-6 rounded-3xl glass-card bg-amber-500/5 border-amber-500/10 flex flex-col justify-between relative overflow-hidden">
                    <div className="relative z-10">
                         <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-white">Monthly Budget</h3>
                            <CreditCard className="text-amber-400" />
                        </div>
                        <div className="text-4xl font-bold text-white font-display text-glow mb-1">$650<span className="text-lg text-white/50 font-normal">.00</span></div>
                        <p className="text-white/40 text-sm">Remaining: $350.00</p>
                    </div>
                     <div className="absolute -right-4 -bottom-4 opacity-10">
                        <DollarSign size={120} />
                    </div>
                </div>

                {/* Spending Chart */}
                <div className="p-6 rounded-3xl glass-card bg-amber-500/5 border-amber-500/10 md:col-span-2">
                    <h3 className="text-xl font-bold text-white mb-4">Spending by Category</h3>
                    <div className="h-40 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={spendingData}>
                                <Tooltip 
                                     cursor={{fill: 'transparent'}}
                                     contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                                     itemStyle={{ color: '#fff' }}
                                />
                                <Bar dataKey="amount" shape={<CustomBar />}>
                                    {spendingData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={['#F59E0B', '#D97706', '#B45309', '#78350F'][index % 4]} />
                                    ))}
                                </Bar>
                                <XAxis dataKey="category" axisLine={false} tickLine={false} tick={{ fill: '#ffffff60', fontSize: 12 }} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Shopping List */}
            <div className="rounded-3xl glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-white">Wishlist & Groceries</h3>
                    <div className="flex gap-2">
                        <button className="px-3 py-1 rounded-lg bg-white/5 text-white/60 text-sm hover:text-white transition-colors">All</button>
                        <button className="px-3 py-1 rounded-lg bg-amber-500/20 text-amber-400 text-sm border border-amber-500/20">Pending</button>
                        <button className="px-3 py-1 rounded-lg bg-white/5 text-white/60 text-sm hover:text-white transition-colors">Bought</button>
                    </div>
                </div>

                <div className="space-y-3">
                    {items.map((item) => (
                        <div key={item.id} className="group flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-amber-500/30 transition-all">
                            <div className="flex items-center gap-4">
                                <button className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                                    item.status === 'bought' ? 'bg-amber-500 border-amber-500' : 'border-white/20 hover:border-amber-400'
                                }`}>
                                     {item.status === 'bought' && <Plus size={14} className="text-white rotate-45" />}
                                </button>
                                <div>
                                    <h4 className={`text-white font-medium ${item.status === 'bought' ? 'line-through text-white/40' : ''}`}>{item.name}</h4>
                                    <span className="text-xs text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded text-uppercase tracking-wider">{item.category}</span>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-white font-bold">${item.price.toFixed(2)}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </motion.div>
    );
};

export default Shopping;
