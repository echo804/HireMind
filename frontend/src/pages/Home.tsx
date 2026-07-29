import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { Link } from "react-router-dom";
import { api } from "../api/client";

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

  // NOT logged in - show original welcome
  if (!user) {
    return (
      <div>
        <div className="text-center mb-16 pt-8">
          <h2 className="text-4xl font-bold text-slate-800 mb-4">AI 智能面试官</h2>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto">
            基于 AI 的智能面试平台，支持简历解析、模拟面试、实时语音对话
          </p>
          <Link to="/register" className="mt-8 inline-block px-8 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors">
            开始使用
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">简历解析</h3>
            <p className="text-sm text-slate-500">AI 自动解析简历，智能评分，去重检测</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">模拟面试</h3>
            <p className="text-sm text-slate-500">文字/语音面试，AI 出题，智能追问</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">知识库</h3>
            <p className="text-sm text-slate-500">文档上传，向量检索，RAG 问答</p>
          </div>
        </div>
      </div>
    );
  }

  // Logged in - show stats
  const cards = [
    { label: "简历总数", value: stats.resumes ?? "...", icon: "📄", color: "bg-blue-50 text-blue-600" },
    { label: "面试次数", value: stats.interviews ?? "...", icon: "📝", color: "bg-green-50 text-green-600" },
    { label: "本周日程", value: stats.schedules ?? "...", icon: "📅", color: "bg-yellow-50 text-yellow-600" },
    { label: "知识库文档", value: stats.docs ?? "...", icon: "📚", color: "bg-purple-50 text-purple-600" },
  ];

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 mb-1">欢迎回来，{user.nickname || "用户"}</h2>
        <p className="text-slate-500">以下是您的数据概览</p>
      </div>

      {loading ? (
        <CardSkeleton count={4} />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {cards.map(card => (
            <div key={card.label} className="bg-white rounded-xl p-5 shadow-sm">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg mb-3 ${card.color}`}>
                {card.icon}
              </div>
              <p className="text-2xl font-bold text-slate-800">{card.value}</p>
              <p className="text-sm text-slate-400 mt-1">{card.label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">简历解析</h3>
          <p className="text-sm text-slate-500">AI 自动解析简历，智能评分，去重检测</p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">模拟面试</h3>
          <p className="text-sm text-slate-500">文字/语音面试，AI 出题，智能追问</p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">知识库</h3>
          <p className="text-sm text-slate-500">文档上传，向量检索，RAG 问答</p>
        </div>
      </div>
    </div>
  );
}
