import { motion } from 'framer-motion';
import { Mail, FileText, Bot } from 'lucide-react';
import SkillRadarChart from './SkillRadarChart';

interface MatchData {
  candidateName: string;
  role: string;
  score: number;
  skills: {
    matched: string[];
    missing: string[];
    inferred: string[];
  };
  radarData: {
    skills: string[];
    candidate: number[];
    job: number[];
  };
}

export default function MatchCard({ match }: { match: MatchData }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="glass-card rounded-2xl border border-[#2a3050] overflow-hidden"
    >
      <div className="grid grid-cols-1 md:grid-cols-12 gap-0">
        {/* Left Side: Info & Skills */}
        <div className="md:col-span-7 p-6 border-b md:border-b-0 md:border-r border-[#2a3050]">
          <div className="flex justify-between items-start mb-6">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-primary text-white text-lg font-bold shadow-lg shadow-indigo-500/20">
                {match.candidateName.charAt(0)}
              </div>
              <div>
                <h3 className="text-xl font-bold text-white leading-tight">{match.candidateName}</h3>
                <p className="text-sm text-indigo-400 font-medium">{match.role}</p>
              </div>
            </div>
            
            {/* Score Ring */}
            <div className="relative h-14 w-14 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="28" cy="28" r="24" className="stroke-[#1a1f35] stroke-[4px] fill-none" />
                <motion.circle
                  initial={{ strokeDashoffset: 150 }}
                  whileInView={{ strokeDashoffset: 150 - (150 * match.score) / 100 }}
                  viewport={{ once: true }}
                  transition={{ duration: 1.5, ease: "easeOut" }}
                  cx="28" cy="28" r="24"
                  className={`stroke-[4px] fill-none drop-shadow-lg ${
                    match.score >= 90 ? 'stroke-emerald-400' : match.score >= 75 ? 'stroke-indigo-400' : 'stroke-orange-400'
                  }`}
                  style={{ strokeDasharray: 150 }}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute text-sm font-bold text-white">{match.score}</span>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">Matched Skills</p>
              <div className="flex flex-wrap gap-2">
                {match.skills.matched.map(skill => (
                  <span key={skill} className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            
            {(match.skills.missing.length > 0 || match.skills.inferred.length > 0) && (
              <div className="grid grid-cols-2 gap-4 pt-2">
                {match.skills.missing.length > 0 && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">Missing</p>
                    <div className="flex flex-wrap gap-2">
                      {match.skills.missing.map(skill => (
                        <span key={skill} className="px-2.5 py-1 rounded-md text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {match.skills.inferred.length > 0 && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">AI Inferred</p>
                    <div className="flex flex-wrap gap-2">
                      {match.skills.inferred.map(skill => (
                        <span key={skill} className="px-2.5 py-1 rounded-md text-xs font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20">
                          <SparklesIcon size={10} className="inline mr-1" />
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <div className="flex gap-3 mt-6 pt-6 border-t border-[#2a3050]">
            <button className="flex-1 flex justify-center items-center gap-2 py-2 px-4 rounded-xl text-sm font-medium text-white bg-[#2a3050] hover:bg-[#32395b] transition-colors">
              <FileText size={16} /> View Resume
            </button>
            <button className="flex-1 flex justify-center items-center gap-2 py-2 px-4 rounded-xl text-sm font-medium text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors">
              <Bot size={16} /> Ask AI
            </button>
            <button className="flex justify-center items-center p-2 rounded-xl text-slate-400 bg-[#1a1f35] border border-[#2a3050] hover:text-white hover:bg-[#2a3050] transition-colors">
              <Mail size={16} />
            </button>
          </div>
        </div>

        {/* Right Side: Radar Chart */}
        <div className="md:col-span-5 bg-[#0a0e1a]/50 p-6 flex flex-col justify-center min-h-[300px]">
          <h4 className="text-center text-xs font-medium uppercase tracking-wider text-slate-500 mb-4">Competency Map</h4>
          <div className="flex-1 relative">
             <SkillRadarChart
               skills={match.radarData.skills}
               candidateScores={match.radarData.candidate}
               jobScores={match.radarData.job}
             />
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// Inline sparse icon to avoid missing imports
function SparklesIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
      <path d="M5 3v4M3 5h4"/>
    </svg>
  );
}
