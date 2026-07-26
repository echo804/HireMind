import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import Layout from "./components/Layout";
import { ToastProvider } from "./contexts/ToastContext";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ResumeList from "./pages/ResumeList";
import ResumeDetail from "./pages/ResumeDetail";
import InterviewList from "./pages/InterviewList";
import InterviewChat from "./pages/InterviewChat";
import InterviewReport from "./pages/InterviewReport";

import Settings from "./pages/Settings";

import Schedule from "./pages/Schedule";
import KnowledgeBase from "./pages/KnowledgeBase";
import KnowledgeBaseDetail from "./pages/KnowledgeBaseDetail";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/resumes" element={<ResumeList />} />
            <Route path="/resumes/:id" element={<ResumeDetail />} />
            <Route path="/interviews" element={<InterviewList />} />
            <Route path="/interviews/:id" element={<InterviewChat />} />
            <Route path="/interviews/:id/report" element={<InterviewReport />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/schedule" element={<Schedule />} />
            <Route path="/knowledge-base" element={<KnowledgeBase />} />
            <Route path="/knowledge-base/:id" element={<KnowledgeBaseDetail />} />
          </Route>
        </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
