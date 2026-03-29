import { motion } from 'framer-motion';
import { Search, Filter, Mail, ExternalLink, User, Trash2 } from 'lucide-react';
import { useState } from 'react';

const initialCandidates = [
  { id: 1, name: 'Alice Chen', role: 'Frontend Developer', score: 92, status: 'Shortlisted', skills: ['React', 'TypeScript', 'Tailwind'] },
  { id: 2, name: 'Bob Smith', role: 'Backend Engineer', score: 85, status: 'In Review', skills: ['Node.js', 'Python', 'PostgreSQL'] },
  { id: 3, name: 'Charlie Davis', role: 'Full Stack', score: 78, status: 'New', skills: ['Vue', 'Ruby', 'MongoDB'] },
  { id: 4, name: 'Diana Prince', role: 'React Developer', score: 95, status: 'Interviewing', skills: ['React', 'Next.js', 'Framer'] },
  { id: 5, name: 'Evan Wright', role: 'UI/UX Designer', score: 65, status: 'Rejected', skills: ['Figma', 'CSS', 'HTML'] },
];

export default function Candidates() {
  const [searchTerm, setSearchTerm] = useState('');
  const [candidates, setCandidates] = useState(initialCandidates);

  const handleDelete = (id: number) => {
    // In a real app, this would hit the backend: authFetch(`/candidates/${id}`, { method: 'DELETE' })
    if (confirm("Are you sure you want to delete this candidate?")) {
      setCandidates(prev => prev.filter(c => c.id !== id));
    }
  };

  const filteredCandidates = candidates.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Candidates Database</h1>
          <p className="text-sm text-slate-400">Manage and review parsed candidate profiles</p>
        </div>
        <div className="flex gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search candidates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0f1525] border border-[#2a3050] rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
            />
          </div>
          <button className="flex items-center justify-center p-2 rounded-xl bg-[#0f1525] border border-[#2a3050] text-slate-300 hover:text-white hover:bg-[#1a1f35] transition-colors gap-2 px-4 shadow-sm">
            <Filter size={18} />
            <span className="hidden sm:inline text-sm font-medium">Filter</span>
          </button>
        </div>
      </div>

      <div className="glass-card rounded-2xl overflow-hidden border border-[#2a3050]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-[#0f1525] text-xs uppercase text-slate-400 border-b border-[#2a3050]">
              <tr>
                <th className="px-6 py-4 font-medium">Candidate</th>
                <th className="px-6 py-4 font-medium">Role Match</th>
                <th className="px-6 py-4 font-medium">Top Skills</th>
                <th className="px-6 py-4 font-medium">Match Score</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a3050]">
              {filteredCandidates.map((candidate) => (
                <motion.tr 
                  key={candidate.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="hover:bg-[#222842]/50 transition-colors group"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-primary text-white font-bold shadow-lg shadow-indigo-500/20">
                        {candidate.name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-semibold text-white">{candidate.name}</div>
                        <div className="text-xs text-slate-400">ID: {candidate.id.toString().padStart(4, '0')}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-300">{candidate.role}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {candidate.skills.map(skill => (
                        <span key={skill} className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#1a1f35] border border-[#2a3050] text-indigo-300">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 rounded-full bg-[#1a1f35] overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${candidate.score >= 90 ? 'bg-emerald-500' : candidate.score >= 75 ? 'bg-indigo-500' : 'bg-warning'}`}
                          style={{ width: `${candidate.score}%` }}
                        />
                      </div>
                      <span className="font-semibold text-white">{candidate.score}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
                      candidate.status === 'Shortlisted' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                      candidate.status === 'Interviewing' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                      candidate.status === 'Rejected' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                      'bg-slate-500/10 text-slate-300 border-slate-500/20'
                    }`}>
                      {candidate.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-1.5 rounded-lg bg-[#1a1f35] text-slate-400 hover:text-white hover:bg-[#2a3050] transition-colors" title="Send Email"><Mail size={16} /></button>
                      <button className="p-1.5 rounded-lg bg-[#1a1f35] text-slate-400 hover:text-white hover:bg-[#2a3050] transition-colors" title="View Profile"><ExternalLink size={16} /></button>
                      <button 
                        onClick={() => handleDelete(candidate.id)}
                        className="p-1.5 rounded-lg bg-[#1a1f35] text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors" 
                        title="Delete Candidate"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
              {filteredCandidates.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    <User size={48} className="mx-auto mb-4 opacity-20" />
                    No candidates found matching "{searchTerm}"
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
