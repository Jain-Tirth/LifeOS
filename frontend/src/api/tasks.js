import client from './client';

export const getTasks = async (params = {}) => {
    // /api/tasks/?status=todo&priority=high
    return client.get('/tasks/', { params });
};

export const createTask = async (taskData) => {
    return client.post('/tasks/', taskData);
};

export const updateTask = async (id, taskData) => {
    return client.patch(`/tasks/${id}/`, taskData);
};

export const deleteTask = async (id) => {
    return client.delete(`/tasks/${id}/`);
};
