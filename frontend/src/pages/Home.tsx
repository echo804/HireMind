import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import {
  FileText, ClipboardList, Calendar, BookOpen, Bot, Rocket, ArrowRight,
  type LucideIcon,
} from "lucide-react";

import { CardSkeleton } from "../components/Skeleton";

export default function Home() {
  const { user } = useAuth();
  const [stats, setStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    const now = new Date();
    const day = now.getDay();
    const monday = new Date(now);
    monday.setDate(now.getDate() - (day === 0 ? 6 : day - 1));
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    sunday.setHours(23, 59, 59);

    Promise.all([
      api.get<any>("/resumes"),
      api.get<any>("/interviews"),
      api.get<any>(`/schedule/range?start=${monday.toISOString()}&end=${sunday.toISOString()}`),
      api.get<any>("/knowledge"),
    ]).then(([resumes, interviews, schedules, docs]) => {
      setStats({
        resumes: (resumes || []).length,
        interviews: (interviews || []).length,
        schedules: (schedules || []).length,
        docs: (docs || []).length,
      });
    }).catch(() => {}).finally(() => setLoading(false));
  }, [user]);

  // 未登录时由 / 路由渲染独立欢迎页（pages/Welcome.tsx），此处仅处理登录态
  if (!user) return null;

  const cards: { label: string; value: string | number; icon: LucideIcon; to: string }[] = [
    { label: "简历总数", value: stats.resumes ?? "...", icon: FileText, to: "/resumes" },
    { label: "面试次数", value: stats.interviews ?? "...", icon: ClipboardList, to: "/interviews" },
    { label: "本周日程", value: stats.schedules ?? "...", icon: Calendar, to: "/schedule" },
    { label: "知识库文档", value: stats.docs ?? "...", icon: BookOpen, to: "/knowledge-base" },
  ];

  const quickActions: { label: string; desc: string; to: string; icon: LucideIcon }[] = [
    { label: "上传简历", desc: "AI 解析并生成评估", to: "/resumes", icon: FileText },
    { label: "开始模拟面试", desc: "选择岗位，AI 出题", to: "/interviews", icon: Bot },
    { label: "管理知识库", desc: "上传文档增强面试", to: "/knowledge-base", icon: BookOpen },
  ];

  return (
    <div className="app-bg -m-4 p-8 rounded-2xl">
      <div className="flex flex-wrap items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-ink mb-1">欢迎回来，{user.nickname || "用户"}</h2>
          <p className="text-ink-secondary">继续提升你的面试能力</p>
        </div>
        <Link to="/interviews" className="btn-primary">
          + 开始新面试
        </Link>
      </div>

      {loading ? (
        <CardSkeleton count={4} />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {cards.map(card => (
            <Link key={card.label} to={card.to} className="card card-hover block">
              <div className="w-10 h-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
                <card.icon className="w-5 h-5" strokeWidth={1.5} />
              </div>
              <p className="text-2xl font-bold text-ink">{card.value}</p>
              <p className="text-sm text-ink-muted mt-1">{card.label}</p>
            </Link>
          ))}
        </div>
      )}

      {/* 快捷操作 */}
      <div className="mb-8">
        <h3 className="text-sm font-semibold text-ink-muted uppercase tracking-wide mb-3">快捷操作</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map(a => (
            <Link key={a.label} to={a.to} className="card card-hover flex items-center gap-4">
              <div className="w-11 h-11 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
                <a.icon className="w-5 h-5" strokeWidth={1.5} />
              </div>
              <div>
                <p className="font-medium text-ink">{a.label}</p>
                <p className="text-xs text-ink-muted">{a.desc}</p>
              </div>
              <ArrowRight className="w-4 h-4 ml-auto text-ink-disabled" strokeWidth={1.5} />
            </Link>
          ))}
        </div>
      </div>

      {/* 空状态引导 */}
      {(stats.resumes === 0 || stats.interviews === 0) && !loading && (
        <div className="card border-dashed border-2 border-line text-center py-8">
          <Rocket className="w-10 h-10 mx-auto mb-3 text-ink-muted" strokeWidth={1.5} />
          <h3 className="font-semibold text-ink mb-1">
            {stats.resumes === 0 ? "从上传简历开始" : "开始你的第一场模拟面试"}
          </h3>
          <p className="text-sm text-ink-secondary mb-4">
            {stats.resumes === 0
              ? "上传简历后，AI 将为你量身定制面试问题"
              : "选择目标岗位，AI 面试官将根据你的简历展开追问"}
          </p>
          <Link to={stats.resumes === 0 ? "/resumes" : "/interviews"} className="btn-primary">
            {stats.resumes === 0 ? "上传简历" : "去面试"}
          </Link>
        </div>
      )}
    </div>
  );
}
