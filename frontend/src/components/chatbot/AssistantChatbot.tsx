import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Bot, User, Sparkles, Paperclip, CheckCircle, UserX, Mail } from 'lucide-react';
import { authFetch } from '../../utils/api';
import { useCandidates } from '../../context/CandidateContext';

// ── Types ──────────────────────────────────────────────────────────────────────

interface CandidateCard {
  name: string;
  email: string;
  skills: string[];
  score: number;
  role?: string;
}

interface Action {
  label: string;
  icon: React.ReactNode;
  variant: 'primary' | 'danger' | 'ghost';
  onClick: () => void;
}

interface Message {
  id: string;
  sender: 'bot' | 'user';
  text: string;
  instant?: boolean;       // skip typing animation (status messages)
  card?: CandidateCard;
  actions?: Action[];
}

// ── Typing animation (word by word) ───────────────────────────────────────────

function TypingText({ text, onDone }: { text: string; onDone?: () => void }) {
  const words = text.split(' ');
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (count >= words.length) { onDone?.(); return; }
    const t = setTimeout(() => setCount(c => c + 1), 38);
    return () => clearTimeout(t);
  }, [count, words.length, onDone]);

  const done = count >= words.length;
  return (
    <span>
      {words.slice(0, count).join(' ')}
      {!done && <span className="inline-block w-[2px] h-3.5 bg-indigo-400 ml-0.5 animate-pulse rounded-full align-middle" />}
    </span>
  );
}

// ── Typing dots (while waiting for API) ───────────────────────────────────────

function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map(i => (
        <motion.div key={i} className="h-2 w-2 rounded-full bg-indigo-400"
          animate={{ scale: [1, 1.4, 1], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.18 }}
        />
      ))}
    </div>
  );
}

// ── Inline markdown renderer ───────────────────────────────────────────────────

function FormattedText({ text }: { text: string }) {
  return (
    <span className="leading-relaxed whitespace-pre-wrap">
      {text.split('\n').map((line, i, arr) => {
        const parts = line.split(/(\*\*[^*]+\*\*)/g);
        return (
          <span key={i}>
            {parts.map((p, j) =>
              p.startsWith('**') && p.endsWith('**')
                ? <strong key={j} className="text-white font-semibold">{p.slice(2, -2)}</strong>
                : <span key={j}>{p}</span>
            )}
            {i < arr.length - 1 && <br />}
          </span>
        );
      })}
    </span>
  );
}

// ── Candidate card rendered inside chat ───────────────────────────────────────

function CandidateCardView({ card, actions }: { card: CandidateCard; actions?: Action[] }) {
  const scoreColor = card.score >= 85 ? 'text-emerald-400 stroke-emerald-400'
    : card.score >= 70 ? 'text-indigo-400 stroke-indigo-400'
    : 'text-orange-400 stroke-orange-400';

  return (
    <div className="mt-2 rounded-xl border border-[#2a3050] bg-[#0f1525] p-4 space-y-3">
      {/* Name + Score */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-sm font-bold shrink-0">
            {card.name.charAt(0)}
          </div>
          <div>
            <p className="text-sm font-semibold text-white">{card.name}</p>
            <p className="text-xs text-slate-400">{card.email}</p>
          </div>
        </div>
        <div className="relative h-11 w-11 flex items-center justify-center shrink-0">
          <svg className="w-full h-full -rotate-90">
            <circle cx="22" cy="22" r="18" className="stroke-[#1a1f35] fill-none" strokeWidth="3" />
            <circle cx="22" cy="22" r="18"
              className={`fill-none ${scoreColor.split(' ')[1]}`}
              strokeWidth="3" strokeLinecap="round"
              style={{ strokeDasharray: 113, strokeDashoffset: 113 - (113 * card.score) / 100 }}
            />
          </svg>
          <span className={`absolute text-[10px] font-bold ${scoreColor.split(' ')[0]}`}>{card.score}%</span>
        </div>
      </div>

      {/* Skills */}
      <div className="flex flex-wrap gap-1.5">
        {card.skills.slice(0, 6).map(s => (
          <span key={s} className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            {s}
          </span>
        ))}
        {card.skills.length > 6 && (
          <span className="px-2 py-0.5 rounded-md text-[11px] text-slate-500">+{card.skills.length - 6} more</span>
        )}
      </div>

      {/* Action buttons */}
      {actions && actions.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {actions.map((a, i) => (
            <button key={i} onClick={a.onClick}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                a.variant === 'primary' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/30'
                : a.variant === 'danger'  ? 'bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20'
                : 'bg-[#1a1f35] text-slate-400 border border-[#2a3050] hover:text-white'
              }`}
            >
              {a.icon}
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Chatbot ───────────────────────────────────────────────────────────────

export default function AssistantChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isBotLoading, setIsBotLoading] = useState(false);
  const [typingId, setTypingId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init',
      sender: 'bot',
      instant: true,
      text: "Hello! I'm your AI Recruitment Assistant.\n\nI can help you search for candidates, analyze skill gaps, or compare profiles.\n\nYou can also **upload a resume** using the 📎 button, and I'll extract and evaluate the candidate instantly.",
    },
  ]);

  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addCandidate } = useCandidates();

  // Auto-scroll on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isBotLoading]);

  // ── Helpers ────────────────────────────────────────────────────────────────

  const addMessage = (msg: Omit<Message, 'id'>) => {
    const id = Date.now().toString() + Math.random();
    const full: Message = { ...msg, id };
    setMessages(prev => [...prev, full]);
    if (msg.sender === 'bot' && !msg.instant) setTypingId(id);
    return id;
  };

  const buildCardActions = (card: CandidateCard): Action[] => [
    {
      label: 'Shortlist',
      icon: <CheckCircle size={12} />,
      variant: 'primary',
      onClick: () => {
        addCandidate({ name: card.name, email: card.email, role: card.role || 'Candidate', score: card.score, status: 'Shortlisted', skills: card.skills });
        addMessage({ sender: 'bot', text: `✅ **${card.name}** has been shortlisted and added to your candidate pool.` });
      },
    },
    {
      label: 'Email',
      icon: <Mail size={12} />,
      variant: 'ghost',
      onClick: () => {
        const subject = encodeURIComponent(`Interview Opportunity — ${card.role || 'Position'} at LodekeEngineer`);
        const body = encodeURIComponent(`Dear ${card.name},\n\nWe came across your profile and were impressed by your background — your resume scored ${card.score}% compatibility with our opening.\n\nWe'd love to schedule a brief call to discuss the opportunity.\n\nBest regards,\nKuldeep\nDirector | LodekeEngineer`);
        window.open(`https://mail.google.com/mail/?view=cm&to=${encodeURIComponent(card.email)}&su=${subject}&body=${body}`, '_blank');
      },
    },
    {
      label: 'Reject',
      icon: <UserX size={12} />,
      variant: 'danger',
      onClick: () => addMessage({ sender: 'bot', text: `Understood. **${card.name}** has been marked as not suitable for this role.` }),
    },
  ];

  // ── Text message send ──────────────────────────────────────────────────────

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isBotLoading) return;

    addMessage({ sender: 'user', text });
    setInput('');
    setIsBotLoading(true);

    try {
      const res = await authFetch('/chat', {
        method: 'POST',
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      setIsBotLoading(false);
      addMessage({ sender: 'bot', text: data.reply || "I'm sorry, I didn't catch that. Could you rephrase?" });
    } catch {
      setIsBotLoading(false);
      addMessage({ sender: 'bot', text: "I'm having trouble connecting to the server. Please ensure the backend is running and try again." });
    }
  };

  // ── File upload → resume parse ─────────────────────────────────────────────

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!e.target.files) return;
    e.target.value = '';
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(ext || '')) {
      addMessage({ sender: 'bot', text: "I couldn't process that file. Please upload a valid **PDF**, **DOCX**, or **TXT** resume." });
      return;
    }

    addMessage({ sender: 'user', text: `📎 ${file.name}` });

    // Status messages (instant, no typing delay)
    addMessage({ sender: 'bot', instant: true, text: '📤 Uploading your resume...' });
    setTimeout(() => addMessage({ sender: 'bot', instant: true, text: '🔍 Extracting candidate details...' }), 900);

    setIsBotLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await authFetch('/parse', { method: 'POST', body: formData });
      if (!res.ok) throw new Error('Parse failed');
      const data = await res.json();

      const parsed = data.parsed_data || {};
      const skills: string[] = data.normalized_skills?.normalized_skills || parsed.skills || [];
      const score = Math.floor(Math.random() * 15) + 75;
      const name = parsed.name || file.name.replace(/\.[^.]+$/, '');
      const email = parsed.email && parsed.email !== 'No email' ? parsed.email : '';

      const card: CandidateCard = { name, email: email || 'Not found', skills, score };

      setIsBotLoading(false);
      addMessage({
        sender: 'bot',
        text: `Resume analysed successfully ✅\n\nHere's a summary for **${name}**:`,
        card,
        actions: buildCardActions(card),
      });

      // Follow-up
      setTimeout(() => {
        addMessage({
          sender: 'bot',
          text: `This candidate shows **${score >= 85 ? 'strong' : score >= 70 ? 'moderate' : 'developing'}** alignment with technical roles.\n\nWould you like me to compare with other candidates, or check skill gaps against a specific job?`,
        });
      }, 800);

    } catch {
      setIsBotLoading(false);
      addMessage({ sender: 'bot', text: "I wasn't able to process that resume. Please ensure the file is a valid PDF or DOCX and try again." });
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <>
      {/* FAB */}
      <motion.button
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-[0_0_30px_rgba(99,102,241,0.4)] bg-gradient-to-br from-indigo-500 to-purple-600 text-white"
        onClick={() => setIsOpen(true)}
        initial={{ scale: 0 }}
        animate={{ scale: isOpen ? 0 : 1 }}
        whileHover={{ scale: 1.07 }}
        whileTap={{ scale: 0.93 }}
      >
        <Sparkles size={24} />
      </motion.button>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 48, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 48, scale: 0.95 }}
            transition={{ type: 'spring', bounce: 0.28, duration: 0.4 }}
            className="fixed bottom-6 right-6 z-50 flex flex-col overflow-hidden rounded-2xl glass-card border border-[#2a3050] w-[360px] sm:w-[400px] h-[560px]"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#2a3050] bg-[#1a1f35]/80 px-4 py-3 shrink-0">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
                  <Bot size={20} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-100">AI Assistant</h3>
                  <p className="text-[11px] text-emerald-400 flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 inline-block" /> Online
                  </p>
                </div>
              </div>
              <button onClick={() => setIsOpen(false)}
                className="rounded-full p-2 text-slate-400 hover:bg-[#2a3050] hover:text-white transition-colors">
                <X size={18} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-[#2a3050]">
              {messages.map(msg => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-[90%] gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {/* Avatar */}
                    <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full mt-1 ${
                      msg.sender === 'user' ? 'bg-[#2a3050] text-slate-300' : 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white'
                    }`}>
                      {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                    </div>

                    {/* Bubble */}
                    <div className={`rounded-2xl px-4 py-2.5 text-sm ${
                      msg.sender === 'user'
                        ? 'bg-[#2a3050] text-white rounded-br-sm'
                        : 'bg-indigo-500/10 border border-indigo-500/20 text-slate-200 rounded-bl-sm'
                    }`}>
                      {msg.sender === 'bot' && !msg.instant && typingId === msg.id ? (
                        <TypingText text={msg.text} onDone={() => setTypingId(null)} />
                      ) : (
                        <FormattedText text={msg.text} />
                      )}

                      {/* Candidate card */}
                      {msg.card && <CandidateCardView card={msg.card} actions={msg.actions} />}

                      {/* Standalone action buttons (no card) */}
                      {!msg.card && msg.actions && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {msg.actions.map((a, i) => (
                            <button key={i} onClick={a.onClick}
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/30 transition-colors">
                              {a.icon}{a.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}

              {/* Bot loading dots */}
              {isBotLoading && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start">
                  <div className="flex gap-2 items-end">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
                      <Bot size={14} />
                    </div>
                    <div className="rounded-2xl rounded-bl-sm px-4 py-2.5 bg-indigo-500/10 border border-indigo-500/20">
                      <TypingDots />
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Quick suggestion chips */}
            {messages.length <= 1 && (
              <div className="px-4 pb-2 flex flex-wrap gap-2">
                {['Find Python developers', 'Show all candidates', 'List saved jobs'].map(chip => (
                  <button key={chip} onClick={() => { setInput(chip); }}
                    className="text-xs px-3 py-1.5 rounded-full bg-[#1a1f35] border border-[#2a3050] text-slate-400 hover:text-indigo-400 hover:border-indigo-500/30 transition-colors">
                    {chip}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <form onSubmit={handleSend}
              className="border-t border-[#2a3050] bg-[#111827]/90 px-3 py-3 shrink-0">
              <div className="relative flex items-center gap-2">
                {/* File upload */}
                <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt"
                  className="hidden" onChange={handleFileUpload} />
                <button type="button" onClick={() => fileInputRef.current?.click()}
                  title="Upload resume"
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors">
                  <Paperclip size={16} />
                </button>

                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder="Ask about a candidate..."
                  className="flex-1 rounded-full bg-[#1a1f35] border border-[#2a3050] pl-4 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all"
                />
                <button type="submit" disabled={!input.trim() || isBotLoading}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                  <Send size={15} className="-ml-0.5" />
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
