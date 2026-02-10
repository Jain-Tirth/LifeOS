import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { initCSRF } from './api/client';
import Layout from './components/layout/Layout';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import Dashboard from './pages/Dashboard/Dashboard';
import Chat from './pages/Chat/Chat';
import Productivity from './pages/Productivity/Productivity';
import Wellness from './pages/Wellness/Wellness';
import Study from './pages/Study/Study';
import MealPlanner from './pages/MealPlanner/MealPlanner';
import Shopping from './pages/Shopping/Shopping';
import './index.css';

const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();
    
    if (loading) return <div className="flex h-screen items-center justify-center bg-slate-900 text-white">Loading...</div>;
    
    if (!user) return <Navigate to="/login" />;
    
    return <Layout>{children}</Layout>;
};

function App() {
  useEffect(() => {
    // Initialize CSRF token on app load
    initCSRF();
  }, []);
  
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/chat" element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          } />
          <Route path="/productivity" element={
            <ProtectedRoute>
              <Productivity />
            </ProtectedRoute>
          } />
          <Route path="/wellness" element={
            <ProtectedRoute>
              <Wellness />
            </ProtectedRoute>
          } />
          <Route path="/study" element={
            <ProtectedRoute>
              <Study />
            </ProtectedRoute>
          } />
          <Route path="/meals" element={
            <ProtectedRoute>
              <MealPlanner />
            </ProtectedRoute>
          } />
          <Route path="/shopping" element={
            <ProtectedRoute>
              <Shopping />
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
