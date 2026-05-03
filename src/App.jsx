import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import UploadResume from './pages/UploadResume';
import JobDescription from './pages/JobDescription';
import Dashboard from './pages/Dashboard';
import CandidateProfile from './pages/CandidateProfile';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background text-text-main font-sans selection:bg-primary/30">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<UploadResume />} />
            <Route path="/job-description" element={<JobDescription />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/candidate/:id" element={<CandidateProfile />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
