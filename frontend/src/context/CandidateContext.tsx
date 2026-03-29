import { createContext, useState, useContext, useEffect, type ReactNode } from 'react';

export interface Candidate {
  id: string;
  name: string;
  email: string;
  role: string;
  score: number;
  status: string;
  skills: string[];
}

interface CandidateContextType {
  candidates: Candidate[];
  addCandidate: (candidate: Omit<Candidate, 'id'>) => void;
  deleteCandidate: (id: string) => void;
}

const CandidateContext = createContext<CandidateContextType | undefined>(undefined);

export function CandidateProvider({ children }: { children: ReactNode }) {
  const [candidates, setCandidates] = useState<Candidate[]>(() => {
    const saved = localStorage.getItem('resumatch_candidates');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return [];
      }
    }
    return [];
  });

  useEffect(() => {
    localStorage.setItem('resumatch_candidates', JSON.stringify(candidates));
  }, [candidates]);

  const addCandidate = (candidateData: Omit<Candidate, 'id'>) => {
    const newCandidate = {
      ...candidateData,
      id: crypto.randomUUID(),
    };
    setCandidates((prev) => [...prev, newCandidate]);
  };

  const deleteCandidate = (id: string) => {
    setCandidates((prev) => prev.filter(c => c.id !== id));
  };

  return (
    <CandidateContext.Provider value={{ candidates, addCandidate, deleteCandidate }}>
      {children}
    </CandidateContext.Provider>
  );
}

export function useCandidates() {
  const context = useContext(CandidateContext);
  if (context === undefined) {
    throw new Error('useCandidates must be used within a CandidateProvider');
  }
  return context;
}
