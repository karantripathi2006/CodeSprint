import { motion, AnimatePresence } from 'framer-motion';
import { Mail, FileText, Bot, X } from 'lucide-react';
import { useState } from 'react';
import { createPortal } from 'react-dom';
import SkillRadarChart from './SkillRadarChart';
import { useCandidates } from '../../context/CandidateContext';

interface MatchData {
  candidateName: string;
  email?: string;
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
  const [showAIInsights, setShowAIInsights] = useState(false);
  const [showEmailPrompt, setShowEmailPrompt] = useState(false);
  const [manualEmail, setManualEmail] = useState('');
  const { candidates } = useCandidates();

  // Find original candidate to access CV if exists
  const candidate = candidates.find(c => c.name === match.candidateName);
  const rawEmail = match.email || candidate?.email;
  const candidateEmail = rawEmail && rawEmail !== 'No email' ? rawEmail : null;

  const handleMailClick = () => {
    if (candidateEmail) {
      window.open(buildGmailUrl(match.candidateName, match.role, match.score, match.skills.matched, candidateEmail), '_blank');
    } else {
      setShowEmailPrompt(true);
    }
  };

  const handleManualSend = () => {
    const email = manualEmail.trim();
    if (!email) return;
    window.open(buildGmailUrl(match.candidateName, match.role, match.score, match.skills.matched, email), '_blank');
    setShowEmailPrompt(false);
    setManualEmail('');
  };

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
            {candidate?.cvData && candidate?.cvFileName ? (
              <a 
                href={candidate.cvData} 
                download={candidate.cvFileName}
                className="flex-1 flex justify-center items-center gap-2 py-2 px-4 rounded-xl text-sm font-medium text-white bg-[#2a3050] hover:bg-[#32395b] transition-colors"
                title={`Download ${candidate.cvFileName}`}
              >
                <FileText size={16} /> View Resume
              </a>
            ) : (
              <button 
                disabled
                title="No CV attached"
                className="flex-1 flex justify-center items-center gap-2 py-2 px-4 rounded-xl text-sm font-medium text-slate-400 bg-[#1a1f35] border border-[#2a3050] opacity-50 cursor-not-allowed"
              >
                <FileText size={16} /> No Resume
              </button>
            )}
            
            <button 
              onClick={() => setShowAIInsights(true)}
              className="flex-1 flex justify-center items-center gap-2 py-2 px-4 rounded-xl text-sm font-medium text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors"
            >
              <Bot size={16} /> Ask AI
            </button>
            <button
              onClick={handleMailClick}
              title={candidateEmail ? `Email ${match.candidateName} (${candidateEmail})` : 'Enter email to contact candidate'}
              className="flex justify-center items-center p-2 rounded-xl text-slate-400 bg-[#1a1f35] border border-[#2a3050] hover:text-indigo-400 hover:bg-indigo-500/10 hover:border-indigo-500/30 transition-colors"
            >
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

      {/* AI Insights Modal */}
      {typeof document !== 'undefined' && createPortal(
        <AnimatePresence>
          {showAIInsights && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowAIInsights(false)}
              className="absolute inset-0 bg-[#0f1525]/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative w-full max-w-lg bg-[#0f1525] border border-[#2a3050] rounded-2xl p-6 shadow-2xl z-10"
            >
              <button 
                onClick={() => setShowAIInsights(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors p-2"
              >
                <X size={20} />
              </button>
              
              <div className="flex items-center gap-3 mb-6">
                 <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400">
                   <Bot size={24} />
                 </div>
                 <div>
                   <h2 className="text-xl font-bold text-white">AI Candidate Insights</h2>
                   <p className="text-sm text-slate-400">Analysis for {match.candidateName}</p>
                 </div>
              </div>

              <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
                 <div className="p-4 bg-[#1a1f35] rounded-xl border border-[#2a3050]">
                   <p>
                     <strong className="text-white">Summary:</strong> {match.candidateName} shows strong foundational alignment for the <span className="text-indigo-300 font-medium">{match.role}</span> role with an overall match score of {match.score}%.
                   </p>
                 </div>
                 
                 {match.skills.missing.length > 0 && (
                   <div className="p-4 bg-red-500/5 rounded-xl border border-red-500/20">
                     <p>
                       <strong className="text-red-400">Attention Area:</strong> The candidate lacks explicit experience with <span className="font-medium text-slate-200">{match.skills.missing.join(", ")}</span>. Consider probing how they plan to bridge this gap during the interview.
                     </p>
                   </div>
                 )}

                 {match.skills.inferred.length > 0 && (
                   <div className="p-4 bg-orange-500/5 rounded-xl border border-orange-500/20">
                     <p>
                       <strong className="text-orange-400">Hidden Potential:</strong> My semantic vectors infer they likely possess <span className="font-medium text-slate-200">{match.skills.inferred.join(", ")}</span> based on adjacent skills in their profile.
                     </p>
                   </div>
                 )}

                 <div className="mt-4 p-4 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
                    <p className="font-bold text-indigo-400 mb-2 flex items-center gap-1.5">
                      <SparklesIcon size={14} /> Suggested Interview Question
                    </p>
                    <p className="italic text-slate-300 text-sm">
                      "Could you walk me through a complex problem you solved using <span className="text-white font-medium">{match.skills.matched[0] || 'your core skills'}</span>, and describe how you structured your approach to deliver the solution?"
                    </p>
                 </div>
              </div>
            </motion.div>
          </div>
        )}
        </AnimatePresence>,
        document.body
      )}

      {/* Email Prompt Modal — shown when no email is on record */}
      {typeof document !== 'undefined' && createPortal(
        <AnimatePresence>
          {showEmailPrompt && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                onClick={() => setShowEmailPrompt(false)}
                className="absolute inset-0 bg-[#0f1525]/80 backdrop-blur-sm"
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
                className="relative w-full max-w-sm bg-[#0f1525] border border-[#2a3050] rounded-2xl p-6 shadow-2xl z-10"
              >
                <button onClick={() => setShowEmailPrompt(false)} className="absolute top-4 right-4 text-slate-400 hover:text-white p-2">
                  <X size={18} />
                </button>
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400">
                    <Mail size={20} />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">Email {match.candidateName}</h3>
                    <p className="text-xs text-slate-400">No email found — enter one to continue</p>
                  </div>
                </div>
                <input
                  type="email"
                  value={manualEmail}
                  onChange={e => setManualEmail(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleManualSend()}
                  placeholder="candidate@email.com"
                  className="w-full bg-[#1a1f35] border border-[#2a3050] rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 mb-3"
                  autoFocus
                />
                <button
                  onClick={handleManualSend}
                  disabled={!manualEmail.trim()}
                  className="w-full py-2.5 rounded-xl text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Open in Mail App
                </button>
              </motion.div>
            </div>
          )}
        </AnimatePresence>,
        document.body
      )}
    </motion.div>
  );
}

function buildGmailUrl(
  name: string,
  role: string,
  score: number,
  matchedSkills: string[],
  email: string,
): string {
  const subject = encodeURIComponent(`Interview Opportunity — ${role} Position at LodekeEngineer`);

  const skillsLine = matchedSkills.length > 0
    ? `Your background in ${matchedSkills.slice(0, 3).join(', ')} caught our attention.`
    : 'Your profile stood out to us.';

  const body = encodeURIComponent(
`Dear ${name},

I hope this message finds you well.

My name is Kuldeep and I am a Director at LodekeEngineer. We came across your profile and were impressed — your resume scored ${score}% compatibility with our ${role} opening.

${skillsLine}

We would love to schedule a brief call to discuss the opportunity in more detail. Please let me know your availability for a 30-minute conversation at your earliest convenience.

Role: ${role}
Match Score: ${score}%

Looking forward to hearing from you.

Best regards,
Kuldeep
Director | LodekeEngineer
+91 8600000010 | LodekeEngineer.com`
  );

  return `https://mail.google.com/mail/?view=cm&to=${encodeURIComponent(email)}&su=${subject}&body=${body}`;
}

// Inline sparse icon to avoid missing imports
function SparklesIcon({ size = 16, className = '', ...rest }: { size?: number; className?: string; [key: string]: any }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }} className={className} {...rest}>
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
      <path d="M5 3v4M3 5h4"/>
    </svg>
  );
}
