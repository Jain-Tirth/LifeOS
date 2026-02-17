import React from 'react';
import { ArrowDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ScrollToBottom = ({ show, onClick }) => {
    return (
        <AnimatePresence>
            {show && (
                <motion.button
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 20 }}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={onClick}
                    className="fixed bottom-24 right-8 p-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg hover:shadow-xl transition-shadow z-30"
                    title="Scroll to bottom"
                >
                    <ArrowDown size={20} />
                </motion.button>
            )}
        </AnimatePresence>
    );
};

export default ScrollToBottom;
