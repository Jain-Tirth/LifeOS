import client from './client';

export const getMealPlans = async (params = {}) => {
    return client.get('/meal-plans/', { params });
};

export const createMealPlan = async (mealData) => {
    return client.post('/meal-plans/', mealData);
};
