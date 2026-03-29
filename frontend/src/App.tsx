import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { CandidateProvider } from './context/CandidateContext';
import DashboardLayout from './components/layout/DashboardLayout';
import ParseResume from './pages/ParseResume';
import Candidates from './pages/Candidates';
import JobMatch from './pages/JobMatch';
import Login from './pages/Login';

function App() {
  return (
    <CandidateProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          {/* Main Dashboard Layout includes Sidebar and Chatbot */}
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Navigate to="/parse" replace />} />
            <Route path="parse" element={<ParseResume />} />
            <Route path="candidates" element={<Candidates />} />
            <Route path="match" element={<JobMatch />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </CandidateProvider>
  );
}

export default App;
