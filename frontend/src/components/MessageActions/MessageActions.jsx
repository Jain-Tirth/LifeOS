import React, { useState } from 'react';
import { Copy, Trash2, RefreshCw, Check } from 'lucide-react';
import { motion } from 'framer-motion';

const MessageActions = ({ message, onCopy, onDelete, onRegenerate, showRegenerate = false }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(message);
            setCopied(true);
            onCopy?.();
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleCopy}
                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-all"
                title="Copy message"
            >
                {copied ? <Check size={14} /> : <Copy size={14} />}
            </motion.button>

            {showRegenerate && (
                <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={onRegenerate}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-all"
                    title="Regenerate response"
                >
                    <RefreshCw size={14} />
                </motion.button>
            )}

            <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={onDelete}
                className="p-1.5 rounded-lg bg-white/5 hover:bg-red-500/20 text-white/60 hover:text-red-400 transition-all"
                title="Delete message"
            >
                <Trash2 size={14} />
            </motion.button>
        </div>
    );
};

export default MessageActions;
