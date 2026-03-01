import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
    LayoutDashboard, 
    MessageSquare, 
    Calendar, 
    BookOpen, 
    Heart, 
    ShoppingBag, 
    LogOut,
    Menu,
    Bell
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const SidebarItem = ({ icon: Icon, label, path, active }) => (
    <Link 
        to={path} 
        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
            active 
                ? 'bg-white/20 text-white shadow-lg backdrop-blur-sm' 
                : 'text-white/70 hover:bg-white/10 hover:text-white'
        }`}
    >
        <Icon size={20} />
        <span className="font-medium">{label}</span>
    </Link>
);

const Layout = ({ children }) => {
    const { user, logout } = useAuth();
    const location = useLocation();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
        { icon: MessageSquare, label: 'Orchestrator', path: '/chat' },
        { icon: Calendar, label: 'Tasks', path: '/productivity' }, // Placeholder route
        { icon: BookOpen, label: 'Study', path: '/study' }, // Placeholder route
        { icon: Heart, label: 'Wellness', path: '/wellness' }, // Placeholder route
        { icon: ShoppingBag, label: 'Meals', path: '/meals' }, // Placeholder route
    ];

    return (
        <div className="flex min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            {/* Desktop Sidebar */}
            <aside className="hidden lg:flex flex-col w-72 p-6 glass-sidebar border-r border-white/10 bg-black/20 backdrop-blur-xl fixed h-full z-20">
                <div className="flex items-center gap-3 mb-10 px-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center">
                        <span className="text-white font-bold text-lg">L</span>
                    </div>
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70 tracking-tight font-display">
                        LifeOS
                    </h1>
                </div>

                <nav className="flex-1 flex flex-col gap-2">
                    {navItems.map((item) => (
                        <SidebarItem 
                            key={item.path}
                            {...item}
                            active={location.pathname === item.path}
                        />
                    ))}
                </nav>

                <div className="mt-auto pt-6 border-t border-white/10">
                    <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 border border-white/5 mb-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-yellow-400 to-orange-500 flex items-center justify-center text-white font-bold text-xs">
                            {user?.first_name?.[0] || 'U'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">
                                {user?.first_name || 'User'}
                            </p>
                            <p className="text-xs text-white/50 truncate">
                                {user?.email}
                            </p>
                        </div>
                    </div>
                    <button 
                        onClick={logout}
                        className="flex items-center gap-3 px-4 py-2 text-red-400 hover:bg-red-400/10 rounded-lg w-full transition-colors text-sm"
                    >
                        <LogOut size={16} />
                        Logout
                    </button>
                </div>
            </aside>

            {/* Mobile Header */}
            <header className="lg:hidden fixed top-0 w-full z-30 px-6 py-4 bg-black/20 backdrop-blur-xl border-b border-white/10 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center">
                        <span className="text-white font-bold">L</span>
                    </div>
                    <h1 className="text-xl font-bold text-white font-display">LifeOS</h1>
                </div>
                <div className="flex items-center gap-4">
                    {/* <button 
                        onClick={() => alert('No new notifications')}
                        className="relative p-2 text-white/70 hover:text-white transition-colors"
                     >
                        <Bell size={20} />
                        <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    </button> */}
                    <button 
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                        className="p-2 text-white"
                    >
                        <Menu size={24} />
                    </button>
                </div>
            </header>

            {/* Mobile Menu Overlay */}
            {isMobileMenuOpen && (
                <div className="fixed inset-0 z-40 bg-slate-900/95 backdrop-blur-lg pt-24 px-6 lg:hidden">
                    <nav className="flex flex-col gap-2">
                        {navItems.map((item) => (
                            <Link 
                                key={item.path}
                                to={item.path}
                                onClick={() => setIsMobileMenuOpen(false)}
                                className={`flex items-center gap-4 px-4 py-4 rounded-xl text-lg ${
                                    location.pathname === item.path
                                        ? 'bg-white/20 text-white'
                                        : 'text-white/70'
                                }`}
                            >
                                <item.icon size={24} />
                                {item.label}
                            </Link>
                        ))}
                        <button 
                            onClick={logout}
                            className="flex items-center gap-4 px-4 py-4 text-red-400 mt-4 border-t border-white/10"
                        >
                            <LogOut size={24} />
                            Logout
                        </button>
                    </nav>
                </div>
            )}

            {/* Main Content */}
            <main className="flex-1 lg:ml-72 h-screen overflow-hidden pt-20 lg:pt-4 p-4 lg:p-6 lg:pb-0">
                <div className="max-w-7xl mx-auto flex flex-col h-full overflow-hidden">
                    {/* Desktop Header Actions */}
                    <div className="hidden lg:flex justify-end items-center mb-0 gap-4 absolute top-6 right-6 z-50">
                         {/* <button 
                            onClick={() => alert('No new notifications')}
                            className="relative p-3 rounded-full bg-white/5 border border-white/10 text-white/70 hover:text-white hover:bg-white/10 transition-all hover:scale-105"
                         >
                            <Bell size={20} />
                            <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full animate-ping"></span>
                            <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full"></span>
                        </button> */}
                    </div>
                    <div className="flex-1 overflow-y-auto w-full pb-6 scroll-gpu scroll-smooth">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Layout;
