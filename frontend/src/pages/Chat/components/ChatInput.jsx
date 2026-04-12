/**
 * ChatInput — detached input bar component.
 * Sprint 3: Chat Monolith Decomposition.
 */
import React from 'react';
import { Mic, ArrowRight } from 'lucide-react';

const ChatInput = ({ input, setInput, inputRef, onSend, onKeyPress, onToggleListen, isListening, disabled }) => (
    <div className="mt-4 relative">
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none -top-20 h-20" />
        <div className="relative flex items-center gap-2 bg-white/10 border border-white/10 p-2 rounded-full backdrop-blur-md">
            {/* Mic button */}
            <button
                onClick={onToggleListen}
                aria-label={isListening ? 'Stop listening' : 'Start voice input'}
                className={`p-3 rounded-full transition-all ${isListening
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-white/5 text-white/70 hover:bg-white/10 hover:text-white'
                    }`}
            >
                {isListening ? (
                    <div className="flex gap-1 h-5 items-center">
                        <span className="w-1 h-3 bg-white rounded-full animate-wave" />
                        <span className="w-1 h-5 bg-white rounded-full animate-wave delay-100" />
                        <span className="w-1 h-3 bg-white rounded-full animate-wave delay-200" />
                    </div>
                ) : (
                    <Mic size={20} />
                )}
            </button>

            {/* Textarea */}
            <textarea
                ref={inputRef}
                id="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyPress}
                className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder-white/40 px-2 resize-none max-h-32 min-h-[24px] overflow-y-auto"
                placeholder="Ask anything — I'll route it to the right agent..."
                rows={1}
                style={{ height: 'auto' }}
                onInput={(e) => {
                    e.target.style.height = 'auto';
                    e.target.style.height = e.target.scrollHeight + 'px';
                }}
            />

            {/* Send button */}
            <button
                id="chat-send-btn"
                onClick={onSend}
                disabled={disabled || !input.trim()}
                aria-label="Send message"
                className="p-3 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-full text-white disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform"
            >
                <ArrowRight size={20} />
            </button>
        </div>
    </div>
);

export default ChatInput;
