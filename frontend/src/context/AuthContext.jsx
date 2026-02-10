import React, { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, register as apiRegister, getProfile, logout as apiLogout } from '../api/auth';
import { useNavigate } from 'react-router-dom';

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
        setUser(data.user);
        return data;
    };

    const register = async (email, password, firstName, lastName) => {
        const data = await apiRegister(email, password, firstName, lastName);
        setUser(data.user);
        return data;
    };

    const logout = () => {
        apiLogout();
        setUser(null);
        window.location.href = '/login';
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};
