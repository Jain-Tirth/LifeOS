import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { requestPasswordReset } from '../../api/auth';
import { useNavigate, Link } from 'react-router-dom';
import { Sparkles, AlertCircle } from 'lucide-react';
import { normalizeErrorMessage } from '../../utils/errorMessage';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [isForgotPassword, setIsForgotPassword] = useState(false);
    const [resetSent, setResetSent] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        
        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (error) {
            setError(normalizeErrorMessage(error.response?.data?.error, 'Login failed. Please check your credentials.'));
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async (e) => {
        e.preventDefault();
        if (!email) {
            setError('Please enter your email address.');
            return;
        }
        setError('');
        setLoading(true);
        
        try {
            await requestPasswordReset(email);
            setResetSent(true);
        } catch (error) {
            setError(normalizeErrorMessage(error.response?.data?.error, 'Failed to send reset link. Please try again.'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            <div className="p-8 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl w-96">
                <div className="flex items-center justify-center gap-2 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center">
                        <Sparkles className="text-white" size={20} />
                    </div>
                    <h1 className="text-2xl font-bold text-white font-display">LifeOS</h1>
                </div>
                
                <h2 className="mb-6 text-xl font-semibold text-center text-white">
                    {isForgotPassword ? 'Reset Password' : 'Welcome Back'}
                </h2>
                
                {error && (
                    <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg flex items-center gap-2 text-red-200">
                        <AlertCircle size={16} />
                        <span className="text-sm">{error}</span>
                    </div>
                )}
                
                {isForgotPassword ? (
                    resetSent ? (
                        <div className="text-center">
                            <div className="mb-6 p-4 bg-green-500/20 border border-green-500/50 rounded-lg text-green-200">
                                <p className="text-sm">Password reset link sent! Check your email.</p>
                            </div>
                            <button
                                onClick={() => {
                                    setIsForgotPassword(false);
                                    setResetSent(false);
                                    setError('');
                                }}
                                className="w-full p-3 text-white bg-white/10 border border-white/20 rounded-lg hover:bg-white/20 transition-all font-medium"
                            >
                                Back to Login
                            </button>
                        </div>
                    ) : (
                        <form onSubmit={handleResetPassword}>
                            <p className="mb-4 text-sm text-white/60 text-center">
                                Enter your email address and we'll send you a link to reset your password.
                            </p>
                            <div className="mb-6">
                                <label className="block mb-2 text-sm font-medium text-white/80">Email</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                                    placeholder="your@email.com"
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full mb-4 p-3 text-white bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Sending...' : 'Send Reset Link'}
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setIsForgotPassword(false);
                                    setError('');
                                }}
                                className="w-full p-3 text-white bg-white/10 border border-white/20 rounded-lg hover:bg-white/20 transition-all font-medium"
                            >
                                Back to Login
                            </button>
                        </form>
                    )
                ) : (
                    <form onSubmit={handleSubmit}>
                        <div className="mb-4">
                            <label className="block mb-2 text-sm font-medium text-white/80">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                                placeholder="your@email.com"
                                required
                            />
                        </div>
                        <div className="mb-6">
                            <div className="flex justify-between items-center mb-2">
                                <label className="block text-sm font-medium text-white/80">Password</label>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsForgotPassword(true);
                                        setError('');
                                    }}
                                    className="text-xs text-purple-400 hover:text-purple-300 transition-colors focus:outline-none"
                                >
                                    Forgot password?
                                </button>
                            </div>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                                placeholder="••••••••"
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full p-3 text-white bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>
                )}
                
                {!isForgotPassword && (
                    <div className="mt-6 text-center">
                        <p className="text-white/60 text-sm">
                            Don't have an account?{' '}
                            <Link to="/register" className="text-purple-400 hover:text-purple-300 font-medium">
                                Sign up
                            </Link>
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Login;
