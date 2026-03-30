import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, Mail, ExternalLink, User, Trash2, X, Download, FileText } from 'lucide-react';
import { useState } from 'react';
import { useCandidates, type Candidate } from '../context/CandidateContext';

export default function Candidates() {
  const [searchTerm, setSearchTerm] = useState('');
  const { candidates, deleteCandidate } = useCandidates();
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  const handleDelete = (id: string) => {
    // In a real app, this would hit the backend: authFetch(`/candidates/${id}`, { method: 'DELETE' })
    if (confirm("Are you sure you want to delete this candidate?")) {
      deleteCandidate(id);
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
                        <div className="text-xs text-slate-400">ID: {candidate.id.substring(0, 4).toUpperCase()}</div>
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
                      <button 
                        onClick={() => setSelectedCandidate(candidate)}
                        className="p-1.5 rounded-lg bg-[#1a1f35] text-slate-400 hover:text-white hover:bg-[#2a3050] transition-colors" 
                        title="View Profile"
                      >
                        <ExternalLink size={16} />
                      </button>
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

      {/* Profile Modal */}
      <AnimatePresence>
        {selectedCandidate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedCandidate(null)}
              className="absolute inset-0 bg-[#0f1525]/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative w-full max-w-2xl bg-[#0f1525] border border-[#2a3050] rounded-2xl p-6 shadow-2xl z-10"
            >
              <button 
                onClick={() => setSelectedCandidate(null)}
                className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors p-2"
              >
                <X size={20} />
              </button>
              
              <div className="space-y-6">
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-primary text-white text-2xl font-bold shadow-lg shadow-indigo-500/20">
                    {selectedCandidate.name.charAt(0)}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">{selectedCandidate.name}</h2>
                    <p className="text-sm text-slate-400">{selectedCandidate.email} • {selectedCandidate.role}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                   <div className="bg-[#1a1f35] p-4 rounded-xl border border-[#2a3050]">
                      <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Match Score</h3>
                      <div className="text-2xl font-bold text-white">{selectedCandidate.score}%</div>
                   </div>
                   <div className="bg-[#1a1f35] p-4 rounded-xl border border-[#2a3050]">
                      <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Status</h3>
                      <div className="text-sm font-medium text-indigo-400 mt-1">{selectedCandidate.status}</div>
                   </div>
                </div>

                <div>
                   <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Skills</h3>
                   <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto custom-scrollbar pr-2">
                       {selectedCandidate.skills.map(skill => (
                         <span key={skill} className="px-2.5 py-1 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium">
                           {skill}
                         </span>
                       ))}
                   </div>
                </div>

                {selectedCandidate.cvFileName && selectedCandidate.cvData && (
                   <div>
                       <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Attached Document</h3>
                       <div className="flex items-center justify-between p-4 bg-[#1a1f35] border border-[#2a3050] rounded-xl">
                          <div className="flex items-center gap-3 overflow-hidden">
                             <FileText className="text-emerald-400 flex-shrink-0" size={24} />
                             <span className="text-sm text-slate-300 truncate">{selectedCandidate.cvFileName}</span>
                          </div>
                          <a 
                            href={selectedCandidate.cvData} 
                            download={selectedCandidate.cvFileName}
                            className="flex items-center gap-2 px-4 py-2 bg-[#2a3050] hover:bg-[#343b5e] text-white text-sm font-medium rounded-lg transition-colors flex-shrink-0"
                          >
                             <Download size={16} />
                             Download CV
                          </a>
                       </div>
                   </div>
                )}
                {(!selectedCandidate.cvFileName || !selectedCandidate.cvData) && (
                   <div className="text-slate-500 text-sm italic">
                     No CV attached for this candidate.
                   </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
