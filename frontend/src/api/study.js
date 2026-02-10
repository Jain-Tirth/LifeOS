import client from './client';

export const getStudySessions = async () => {
    return client.get('/study-sessions/');
};

export const createStudySession = async (sessionData) => {
    return client.post('/study-sessions/', sessionData);
};
