import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { ArrowRight } from 'lucide-react';

const BentoCard = ({ 
    title, 
    value, 
    label, 
    icon: Icon, 
    color, 
    className, 
    delay = 0,
    onClick,
    children 
}) => {
    const colorClasses = {
        'card-productivity': 'from-purple-500/20 to-purple-600/20 border-purple-500/30 hover:border-purple-500/50',
        'card-wellness': 'from-teal-500/20 to-teal-600/20 border-teal-500/30 hover:border-teal-500/50',
        'card-study': 'from-blue-500/20 to-blue-600/20 border-blue-500/30 hover:border-blue-500/50',
        'card-meal': 'from-green-500/20 to-green-600/20 border-green-500/30 hover:border-green-500/50',
        'card-shopping': 'from-amber-500/20 to-amber-600/20 border-amber-500/30 hover:border-amber-500/50',
    };

    const iconColors = {
        'card-productivity': 'text-purple-400',
        'card-wellness': 'text-teal-400',
        'card-study': 'text-blue-400',
        'card-meal': 'text-green-400',
        'card-shopping': 'text-amber-400',
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay }}
            className={clsx(
                "group relative p-6 rounded-3xl bg-gradient-to-br backdrop-blur-md border transition-all duration-300 cursor-pointer overflow-hidden",
                colorClasses[color],
                className
            )}
            onClick={onClick}
        >
            <div className="flex justify-between items-start mb-4">
                <div className={clsx("p-3 rounded-2xl bg-white/5", iconColors[color])}>
                    <Icon size={24} />
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity transform group-hover:translate-x-1 duration-300">
                    <ArrowRight className="text-white/50" />
                </div>
            </div>

            <div className="relative z-10">
                <h3 className="text-white/60 font-medium mb-1">{title}</h3>
                <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-white font-display tracking-tight">{value}</span>
                    <span className="text-sm text-white/40">{label}</span>
                </div>
            </div>

            {/* Background Decor */}
            <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-gradient-to-br from-white/5 to-transparent rounded-full blur-2xl" />
            
            {/* Chart Area */}
            <div className="mt-6 h-16 w-full relative">
                {children}
            </div>
        </motion.div>
    );
};

export default BentoCard;
