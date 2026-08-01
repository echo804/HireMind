import { Link, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ErrorBoundary } from "./ErrorBoundary";
import { useState } from "react";

const navItems = [
  { path: "/resumes", label: "简历管理" },
  { path: "/interviews", label: "模拟面试" },
  { path: "/knowledge-base", label: "知识库" },
  { path: "/schedule", label: "面试日程" },
  { path: "/settings", label: "系统设置" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (path: string) =>
    location.pathname.startsWith(path);

  // 登录/注册与未登录首页（欢迎页）为裸布局，不渲染顶栏与内容容器
  if (
    location.pathname === "/login" ||
    location.pathname === "/register" ||
    (location.pathname === "/" && !user)
  ) {
    return <Outlet />;
  }

  return (
    <div className="min-h-screen app-bg">
      <header className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-bold text-ink shrink-0">
              HireMind
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              {navItems.map((item) => (
                <Link key={item.path} to={item.path}
                  className={isActive(item.path) ? "text-sm font-medium pb-1 transition-colors text-brand-600 border-b-2 border-brand-600" : "text-sm font-medium pb-1 transition-colors text-ink-secondary hover:text-brand-600"}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3">
                <span className="text-sm text-ink-secondary hidden sm:inline">{user.nickname}</span>
                <button onClick={logout} className="text-sm text-red-500 hover:underline">退出</button>
              </div>
            ) : (
              <Link to="/login" className="text-sm text-brand-600 hover:underline">登录</Link>
            )}
            <button className="md:hidden p-1" onClick={() => setMenuOpen(!menuOpen)}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {menuOpen ? (
                  <path strokeLinecap="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {menuOpen && (
          <div className="md:hidden border-t border-line">
            <div className="max-w-6xl mx-auto px-4 py-3 flex flex-col gap-3">
              {navItems.map((item) => (
                <Link key={item.path} to={item.path} onClick={() => setMenuOpen(false)}
                  className={isActive(item.path) ? "text-sm font-medium py-1 text-brand-600" : "text-sm font-medium py-1 text-ink-secondary hover:text-brand-600"}>
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  );
}
