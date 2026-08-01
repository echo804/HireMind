import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Layout from "./components/Layout";
import { ToastProvider } from "./contexts/ToastContext";
import Home from "./pages/Home";
import Welcome from "./pages/Welcome";
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

function ProtectedRoute() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/" replace />;
  return <Outlet />;
}

// 首页：已登录显示数据概览，未登录显示欢迎页（全屏，无 Layout 外壳）
function RootRoute() {
  const { user } = useAuth();
  return user ? <Home /> : <Welcome />;
}

// 路由级进出场过渡：欢迎页 ↔ 登录/注册 整页渐隐/浮现
function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <Routes location={location} key={location.pathname}>
        <Route element={<Layout />}>
          <Route path="/" element={<RootRoute />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
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
        </Route>
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
        <AnimatedRoutes />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
