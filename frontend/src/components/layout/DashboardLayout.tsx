import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { FileUp, Users, Target, LogOut, Menu, X, Brain } from 'lucide-react';
import AssistantChatbot from '../chatbot/AssistantChatbot';

export default function DashboardLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate('/login');
  };

  const navLinks = [
    { to: '/parse', icon: <FileUp size={20} />, label: 'Parse Resume' },
    { to: '/candidates', icon: <Users size={20} />, label: 'Candidates' },
    { to: '/match', icon: <Target size={20} />, label: 'Match Job' },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-[color:var(--bg-primary)]">
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        className={`fixed inset-y-0 left-0 z-50 w-64 glass-panel border-r border-[#2a3050] transition-transform duration-300 lg:static lg:translate-x-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between px-6 border-b border-[#2a3050]">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-primary">
              <Brain size={20} className="text-white" />
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
              ResuMatch AI
            </span>
          </div>
          <button onClick={() => setIsSidebarOpen(false)} className="lg:hidden text-gray-400 hover:text-white">
            <X size={24} />
          </button>
        </div>

        <nav className="p-4 space-y-2">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-4 py-3 font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:bg-[#1a1f35] hover:text-slate-200'
                }`
              }
            >
              {link.icon}
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full p-4 border-t border-[#2a3050]">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-xl px-4 py-3 font-medium text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </motion.aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header (Mobile) */}
        <header className="flex h-16 items-center justify-between px-4 sm:px-6 lg:hidden border-b border-[#2a3050] glass">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="text-slate-400 hover:text-white"
          >
            <Menu size={24} />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-primary">
              <Brain size={20} className="text-white" />
            </div>
          </div>
          <div className="w-6" /> {/* Spacer */}
        </header>

        {/* Main Scrollable Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 relative">
          <Outlet />
        </main>
      </div>

      {/* Global Floating Components */}
      <AssistantChatbot />
    </div>
  );
}
