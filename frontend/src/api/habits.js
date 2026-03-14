import client from './client';

export const getHabits = async (params = {}) => {
    return client.get('/habits/', { params });
};

export const createHabit = async (data) => {
    return client.post('/habits/', data);
};

export const updateHabit = async (id, data) => {
    return client.patch(`/habits/${id}/`, data);
};

export const deleteHabit = async (id) => {
    return client.delete(`/habits/${id}/`);
};

export const toggleHabitToday = async (id) => {
    return client.post(`/habits/${id}/toggle_today/`);
};

export const getHabitDigest = async () => {
    return client.get('/habits/daily_digest/');
};
