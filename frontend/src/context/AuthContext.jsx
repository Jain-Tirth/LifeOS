import React, { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, register as apiRegister, getProfile, logout as apiLogout } from '../api/auth';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const initAuth = async () => {
            const token = localStorage.getItem('lifeos_token');
            if (token) {
                try {
                    const response = await getProfile();
                    // Assuming endpoint returns { user: ... } or just user object
                    setUser(response.data);
                } catch (error) {
                    console.error("Failed to fetch profile:", error);
                    localStorage.removeItem('lifeos_token');
                }
            }
            setLoading(false);
        };
        initAuth();
    }, []);

    const login = async (email, password) => {
        const data = await apiLogin(email, password);
        setUser(data.user || { email }); // Fallback if user object not full
        return data;
    };

    const register = async (email, password, firstName, lastName) => {
        const data = await apiRegister(email, password, firstName, lastName);
        return data;
    };

    const logout = () => {
        apiLogout();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};
