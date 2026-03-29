import { motion } from 'framer-motion';
import { Target, Search, FileText, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';
import MatchCard from '../components/match/MatchCard';

// Mock Data
const mockMatches = [
  {
    candidateName: "Alice Chen",
    role: "Frontend Developer",
    score: 92,
    skills: {
      matched: ["React", "TypeScript", "Tailwind", "Problem Solving"],
      missing: ["GraphQL"],
      inferred: ["CSS Architecture"],
    },
    radarData: {
      skills: ["React", "TypeScript", "Problem Solving", "System Design", "Communication"],
      candidate: [95, 90, 85, 70, 95],
      job: [80, 80, 90, 85, 80]
    }
  },
  {
    candidateName: "Bob Smith",
    role: "Backend Engineer",
    score: 85,
    skills: {
      matched: ["Node.js", "Python", "Problem Solving"],
      missing: ["PostgreSQL", "Docker"],
      inferred: ["REST APIs"],
    },
    radarData: {
      skills: ["Node.js", "Python", "Problem Solving", "System Design", "Communication"],
      candidate: [85, 95, 90, 80, 75],
      job: [90, 70, 90, 85, 80]
    }
  }
];

export default function JobMatch() {
  const [isMatching, setIsMatching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleMatch = (e: React.FormEvent) => {
    e.preventDefault();
    setIsMatching(true);
    setShowResults(false);
    
    setTimeout(() => {
      setIsMatching(false);
      setShowResults(true);
    }, 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-7xl mx-auto"
    >
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Target className="text-indigo-400" />
            AI Job Matching
          </h1>
          <p className="text-sm text-slate-400 mt-1">Cross-reference job requirements against candidate vectors</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Job Input Panel */}
        <div className="lg:col-span-4 glass-card p-6 rounded-2xl h-fit border border-[#2a3050]">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/20 text-purple-400">
              <FileText size={20} />
            </div>
            <h2 className="text-lg font-semibold text-white">Job Details</h2>
          </div>

          <form onSubmit={handleMatch} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Job Title</label>
              <input
                required
                defaultValue="Senior Frontend Developer"
                className="w-full bg-[#0f1525] border border-[#2a3050] rounded-xl px-4 py-2.5 text-sm text-white focus:ring-1 focus:ring-indigo-500 transition-colors"
                placeholder="e.g. Senior Frontend Developer"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Required Skills (comma separated)</label>
              <input
                required
                defaultValue="React, TypeScript, GraphQL, System Design"
                className="w-full bg-[#0f1525] border border-[#2a3050] rounded-xl px-4 py-2.5 text-sm text-white focus:ring-1 focus:ring-indigo-500 transition-colors"
                placeholder="e.g. React, Python, AWS"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Job Description</label>
              <textarea
                required
                rows={5}
                defaultValue={"Looking for an experienced developer with strong React and TypeScript skills to lead our frontend architecture. Must have experience with complex state management."}
                className="w-full bg-[#0f1525] border border-[#2a3050] rounded-xl px-4 py-2.5 text-sm text-white focus:ring-1 focus:ring-indigo-500 transition-colors resize-none"
                placeholder="Paste full job description here..."
              />
            </div>
            
            <button
              type="submit"
              disabled={isMatching}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-white bg-gradient-primary disabled:opacity-50 font-medium shadow-lg shadow-indigo-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              {isMatching ? (
                <span className="flex items-center gap-2">
                  <div className="h-4 w-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  Running AI Match...
                </span>
              ) : (
                <>
                  <Search size={18} />
                  Find Matches
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {!showResults && !isMatching && (
            <div className="glass-card rounded-2xl border border-[#2a3050] h-full min-h-[400px] flex flex-col items-center justify-center text-slate-500">
              <Target size={48} className="opacity-20 mb-4" />
              <p>Enter job criteria and run match to see top candidates.</p>
            </div>
          )}

          {isMatching && (
            <div className="glass-card rounded-2xl border border-[#2a3050] h-full min-h-[400px] flex flex-col items-center justify-center bg-[color:var(--bg-card)]">
              <div className="relative w-24 h-24 mb-6">
                 {/* Decorative rings for matching animation */}
                 <div className="absolute inset-0 border-4 border-indigo-500/20 rounded-full animate-ping" />
                 <div className="absolute inset-2 border-4 border-purple-500/40 rounded-full animate-pulse" />
                 <div className="absolute inset-4 bg-gradient-primary rounded-full flex items-center justify-center shadow-lg shadow-indigo-500/40">
                   <Target size={24} className="text-white" />
                 </div>
              </div>
              <p className="text-lg font-semibold text-white mb-2">Calculating semantic vectors...</p>
              <p className="text-sm text-slate-400">Comparing 50+ candidates against criteria</p>
            </div>
          )}

          {showResults && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-6"
            >
              <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 px-4 py-2 rounded-lg border border-emerald-500/20 w-fit">
                <CheckCircle2 size={16} />
                <span className="text-sm font-medium">Found {mockMatches.length} strong matches</span>
              </div>
              
              <div className="grid grid-cols-1 gap-6">
                {mockMatches.map((match, idx) => (
                  <MatchCard key={idx} match={match} />
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
