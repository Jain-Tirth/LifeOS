/**
 * Time formatting utilities for chat UI.
 */

export function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
}

export function getDateSeparator(currentTimestamp, prevTimestamp) {
    if (!prevTimestamp) return 'Today';
    const current = new Date(currentTimestamp);
    const prev = new Date(prevTimestamp);
    const currentDate = current.toDateString();
    const prevDate = prev.toDateString();

    if (currentDate !== prevDate) {
        const today = new Date().toDateString();
        const yesterday = new Date(Date.now() - 86400000).toDateString();
        if (currentDate === today) return 'Today';
        if (currentDate === yesterday) return 'Yesterday';
        return current.toLocaleDateString();
    }
    return null;
}
