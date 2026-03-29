import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Bot, User, Sparkles } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'bot' | 'user';
  text: string;
}

export default function AssistantChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'bot',
      text: 'Hi there! I am your AI Recruitment Assistant. How can I help you analyze candidates today?',
    },
  ]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: input,
    };

    setMessages((prev) => [...prev, newMsg]);
    setInput('');

    // Simulate AI response
    setTimeout(() => {
      let botResponse = "I'm analyzing the data. This candidate seems like a strong match for senior roles.";
      const lowerInput = newMsg.text.toLowerCase();
      
      if (lowerInput.includes('match') || lowerInput.includes('score')) {
        botResponse = "The match score is calculated using semantic similarity between the candidate's parsed skills in the vector DB and your job description.";
      } else if (lowerInput.includes('missing')) {
        botResponse = "Based on the recent job post, the candidate is missing 'Kubernetes' and 'AWS', but they have strong experience in containerization overall.";
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: botResponse,
        },
      ]);
    }, 1000);
  };

  return (
    <>
      {/* Floating Action Button */}
      <motion.button
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-[0_0_30px_rgba(99,102,241,0.4)] bg-gradient-to-br from-indigo-500 to-purple-600 text-white hover:scale-110 transition-transform"
        onClick={() => setIsOpen(true)}
        initial={{ scale: 0 }}
        animate={{ scale: isOpen ? 0 : 1 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Sparkles size={24} />
      </motion.button>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.95 }}
            transition={{ type: 'spring', bounce: 0.3, duration: 0.4 }}
            className="fixed bottom-6 right-6 z-50 flex h-[500px] w-[350px] sm:w-[400px] flex-col overflow-hidden rounded-2xl glass-card border border-[#2a3050] sm:right-6"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#2a3050] bg-[#1a1f35]/80 p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-400">
                  <Bot size={24} />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-100">AI Assistant</h3>
                  <p className="text-xs text-emerald-400 flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block"></span>
                    Online
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-full p-2 text-slate-400 hover:bg-[#2a3050] hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-[85%] gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full mt-auto ${
                      msg.sender === 'user' ? 'bg-[#2a3050] text-slate-300' : 'bg-gradient-primary text-white'
                    }`}>
                      {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                    </div>
                    <div
                      className={`rounded-2xl px-4 py-2.5 text-sm ${
                        msg.sender === 'user'
                          ? 'bg-[#2a3050] text-white rounded-br-sm'
                          : 'bg-indigo-500/10 border border-indigo-500/20 text-slate-200 rounded-bl-sm'
                      }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Input Area */}
            <form
              onSubmit={handleSend}
              className="border-t border-[#2a3050] bg-[#111827]/90 p-3"
            >
              <div className="relative flex items-center">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about a candidate..."
                  className="w-full rounded-full bg-[#1a1f35] border border-[#2a3050] pl-4 pr-12 py-3 text-sm text-white placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all"
                />
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="absolute right-2 flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500 text-white transition-transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
                >
                  <Send size={16} className="-ml-0.5" />
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
