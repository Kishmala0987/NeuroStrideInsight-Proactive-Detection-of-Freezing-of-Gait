import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import HomePage     from './pages/HomePage';
import UploadPage    from './pages/UploadPage';
import SessionPage   from './pages/SessionPage';
import SubjectsPage  from './pages/SubjectsPage';
import SubjectPage   from './pages/SubjectPage';
import StatsPage     from './pages/StatsPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/"                       element={<HomePage />} />
            <Route path="/upload"                 element={<UploadPage />} />
            <Route path="/sessions/:sessionId"    element={<SessionPage />} />
            <Route path="/subjects"               element={<SubjectsPage />} />
            <Route path="/subjects/:subjectId"    element={<SubjectPage />} />
            <Route path="/stats"                  element={<StatsPage />} />
            <Route path="*"                       element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
