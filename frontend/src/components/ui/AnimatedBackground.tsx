import { useEffect } from 'react';
import { motion, useSpring } from 'framer-motion';

export default function AnimatedBackground() {
  // Spring animations for an organic, smooth cursor follow
  const cursorX = useSpring(0, { stiffness: 60, damping: 25 });
  const cursorY = useSpring(0, { stiffness: 60, damping: 25 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      cursorX.set(e.clientX);
      cursorY.set(e.clientY);
    };

    window.addEventListener('mousemove', handleMouseMove);
    // Initialize default position near center to start
    cursorX.set(window.innerWidth / 2);
    cursorY.set(window.innerHeight / 2);
    
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [cursorX, cursorY]);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-[#0a0e1a]">
      {/* 3D Animated Floor Grid */}
      <div 
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #6366f1 1px, transparent 1px),
            linear-gradient(to bottom, #6366f1 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
          animation: 'gridMove 4s linear infinite',
          transformOrigin: 'bottom center',
        }}
      />
      
      {/* 3D Floating Rings */}
      <motion.div
         className="absolute w-96 h-96 border border-indigo-500/10 rounded-full"
         animate={{ 
           rotateX: [0, 360], 
           rotateY: [0, 360],
           z: [0, 150, 0]
         }}
         transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
         style={{ left: '15%', top: '20%', transformStyle: 'preserve-3d', perspective: '1000px' }}
      >
        <div className="w-full h-full border border-purple-500/10 rounded-full absolute" style={{ transform: 'rotateX(45deg) rotateY(45deg)' }}></div>
      </motion.div>
      
      <motion.div
         className="absolute border border-pink-500/10 rounded-full"
         animate={{ 
           rotateX: [360, 0], 
           rotateY: [0, 360],
           z: [0, -150, 0]
         }}
         transition={{ duration: 35, repeat: Infinity, ease: "linear" }}
         style={{ right: '5%', bottom: '10%', width: '30rem', height: '30rem', transformStyle: 'preserve-3d', perspective: '1000px' }}
      >
        <div className="w-full h-full border border-indigo-500/10 rounded-full absolute" style={{ transform: 'rotateX(75deg) rotateY(15deg)' }}></div>
      </motion.div>

      {/* Interactive Cursor Follower - Big Glow Orb */}
      <motion.div
        className="absolute rounded-full"
        style={{
          x: cursorX,
          y: cursorY,
          width: 600,
          height: 600,
          marginLeft: -300,
          marginTop: -300,
          background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, rgba(10,14,26,0) 70%)',
          filter: 'blur(50px)',
        }}
      />
      
      {/* Subtle secondary cursor glow (purpleish) */}
      <motion.div
        className="absolute rounded-full mix-blend-screen"
        style={{
          x: cursorX,
          y: cursorY,
          width: 300,
          height: 300,
          marginLeft: -150,
          marginTop: -150,
          background: 'radial-gradient(circle, rgba(168,85,247,0.12) 0%, rgba(10,14,26,0) 60%)',
          filter: 'blur(30px)',
          transition: 'all 0.1s ease-out' // Gives a slightly delayed, trailing effect
        }}
      />
      
      {/* Interactive Sharp Cursor Dot */}
      <motion.div
        className="absolute rounded-full bg-indigo-400/40 shadow-[0_0_15px_#6366f1]"
        style={{
          x: cursorX,
          y: cursorY,
          width: 6,
          height: 6,
          marginLeft: -3,
          marginTop: -3,
        }}
      />
    </div>
  );
}
