import { motion } from 'framer-motion';
import { Brain } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function ParseLoader() {
  const messages = [
    "Analyzing document structure...",
    "Extracting experience and education...",
    "Normalizing skill taxonomies...",
    "Building semantic profile...",
    "Finalizing multi-agent match..."
  ];

  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 800); // Change text every 800ms to match the 4s total loading time

    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0a0e1a]/80 backdrop-blur-xl"
    >
      <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm w-full">
        {/* Animated Scanner Ring */}
        <div className="relative mb-8 h-32 w-32">
          {/* Outer Ring */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
            className="absolute inset-0 rounded-full border-4 border-dashed border-indigo-500/30"
          />
          {/* Inner Fast Ring */}
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
            className="absolute inset-2 rounded-full border-2 border-dashed border-purple-500/50"
          />
          {/* Center Pulsing Icon */}
          <motion.div
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
            className="absolute inset-0 flex items-center justify-center rounded-full bg-gradient-primary shadow-[0_0_30px_rgba(99,102,241,0.5)]"
          >
            <Brain size={48} className="text-white" />
          </motion.div>
        </div>

        {/* Dynamic Text */}
        <h2 className="mb-2 text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
          AI Agents Working
        </h2>
        <motion.p
          key={messageIndex}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="text-sm text-slate-400 h-6"
        >
          {messages[messageIndex]}
        </motion.p>
        
        {/* Progress Bar Container */}
        <div className="mt-8 h-1 w-full overflow-hidden rounded-full bg-[#1a1f35]">
          <motion.div
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 4, ease: "easeInOut" }}
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"
          />
        </div>
      </div>
    </motion.div>
  );
}
