import client from './client';

export const getWellnessActivities = async (params = {}) => {
    // /api/wellness-activities/?activity_type=exercise
    return client.get('/wellness-activities/', { params });
};

export const logWellnessActivity = async (activityData) => {
    return client.post('/wellness-activities/', activityData);
};
