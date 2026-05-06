export function normalizeErrorMessage(error, fallback = 'Something went wrong.') {
    if (!error) {
        return fallback;
    }

    if (typeof error === 'string') {
        return error;
    }

    if (Array.isArray(error)) {
        return error
            .map((item) => normalizeErrorMessage(item, ''))
            .filter(Boolean)
            .join(', ') || fallback;
    }

    if (typeof error === 'object') {
        return (
            error.message
            || error.detail
            || error.error
            || error.code
            || JSON.stringify(error)
            || fallback
        );
    }

    return String(error);
}