import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Sparkles, AlertCircle } from 'lucide-react';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [passwordConfirm, setPasswordConfirm] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        
        if (password !== passwordConfirm) {
            setError('Passwords do not match');
            return;
        }
        
        if (password.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }
        
        setLoading(true);
        
        try {
            await register(email, password, firstName, lastName);
            navigate('/');
        } catch (error) {
            setError(error.response?.data?.error || error.response?.data?.email?.[0] || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
            <div className="p-8 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl w-full max-w-md">
                <div className="flex items-center justify-center gap-2 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center">
                        <Sparkles className="text-white" size={20} />
                    </div>
                    <h1 className="text-2xl font-bold text-white font-display">LifeOS</h1>
                </div>
                
                <h2 className="mb-6 text-xl font-semibold text-center text-white">Create Account</h2>
                
                {error && (
                    <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg flex items-center gap-2 text-red-200">
                        <AlertCircle size={16} />
                        <span className="text-sm">{error}</span>
                    </div>
                )}
                
                <form onSubmit={handleSubmit}>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <label className="block mb-2 text-sm font-medium text-white/80">First Name</label>
                            <input
                                type="text"
                                value={firstName}
                                onChange={(e) => setFirstName(e.target.value)}
                                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                                placeholder="John"
                            />
                        </div>
                        <div>
                            <label className="block mb-2 text-sm font-medium text-white/80">Last Name</label>
                            <input
                                type="text"
                                value={lastName}
                                onChange={(e) => setLastName(e.target.value)}
                                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                                placeholder="Doe"
                            />
                        </div>
                    </div>
                    
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
                    
                    <div className="mb-4">
                        <label className="block mb-2 text-sm font-medium text-white/80">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                            placeholder="••••••••"
                            required
                        />
                    </div>
                    
                    <div className="mb-6">
                        <label className="block mb-2 text-sm font-medium text-white/80">Confirm Password</label>
                        <input
                            type="password"
                            value={passwordConfirm}
                            onChange={(e) => setPasswordConfirm(e.target.value)}
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
                        {loading ? 'Creating Account...' : 'Sign Up'}
                    </button>
                </form>
                
                <div className="mt-6 text-center">
                    <p className="text-white/60 text-sm">
                        Already have an account?{' '}
                        <Link to="/login" className="text-purple-400 hover:text-purple-300 font-medium">
                            Sign in
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Register;
