import client from './client';

export const getMealPlans = async (params = {}) => {
    return client.get('/meal-plans/', { params });
};

export const createMealPlan = async (mealData) => {
    return client.post('/meal-plans/', mealData);
};

export const deleteMealPlan = async (id) => {
    return client.delete(`/meal-plans/${id}/`);
};

