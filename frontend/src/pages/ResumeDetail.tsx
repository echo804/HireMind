import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";

interface ResumeData {
  id: string; filename: string; file_size: number; file_type: string;
  name: string | null; email: string | null; phone: string | null;
  position: string | null; skills: string[] | null;
  experience: { company: string; title: string; duration: string; description: string }[] | null;
  education: { school: string; degree: string; major: string; year: string }[] | null;
  summary: string | null; score: number | null; progress: number; status: string; created_at: string;
}

export default function ResumeDetail() {
  const { id } = useParams();
  const [resume, setResume] = useState<ResumeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [_error, setError] = useState<string | null>(null);
  const [_pollCount, setPollCount] = useState(0);

  useEffect(function poll() {
    api.get<any>("/resumes/" + id).then(data => {
      setResume(data);
      if (data.status === "done" || data.status === "failed") {
        setLoading(false);
      } else {
        setPollCount(c => c + 1);
        setTimeout(poll, 1500);
      }
    }).catch((e: any) => {
      setError(e.message || "获取简历信息失败");
      setLoading(false);
    });
  }, [id]);

  if (loading && !resume) {
    return (
      <div>
        <Link to="/resumes" className="text-sm text-blue-600 hover:underline">&larr; 返回简历列表</Link>
        <div className="text-center py-16">
          <div className="animate-spin w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full mx-auto mb-4" />
          <p className="text-slate-500">正在上传文件并启动分析...</p>
        </div>
      </div>
    );
  }

  if (!resume) return <div className="text-center py-12 text-slate-400">简历不存在</div>;

  if (resume.status === "processing") {
    const pct = resume.progress || 0;
    const stepLabel = pct < 20 ? "解析 PDF 文本..." :
      pct < 50 ? "AI 智能分析中..." :
      pct < 80 ? "正在提取关键信息..." :
      "正在生成报告...";
    return (
      <div>
        <Link to="/resumes" className="text-sm text-blue-600 hover:underline">&larr; 返回简历列表</Link>
        <div className="text-center py-16">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">AI 正在分析简历</h3>
          <p className="text-sm text-slate-400 mb-6">{stepLabel}</p>
          {/* 百分比进度条 */}
          <div className="max-w-md mx-auto mb-3">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>进度</span><span>{pct}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
              <div className="bg-blue-600 h-3 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${pct}%` }} />
            </div>
          </div>
          {/* 步骤指示器 */}
          <div className="max-w-sm mx-auto space-y-2 mt-6">
            <Step done={pct >= 20} active={pct < 20} label="解析 PDF 文本" />
            <Step done={pct >= 90} active={pct >= 20 && pct < 90} label="AI 智能分析" />
            <Step done={pct === 100} active={pct >= 90 && pct < 100} label="生成报告" />
          </div>
          <p className="text-xs text-slate-400 mt-6">通常需要 10-30 秒，请稍候...</p>
        </div>
      </div>
    );
  }

  if (resume.status === "failed") {
    return (
      <div>
        <Link to="/resumes" className="text-sm text-blue-600 hover:underline">&larr; 返回简历列表</Link>
        <div className="text-center py-16">
          <div className="text-4xl mb-4">&#10060;</div>
          <h3 className="text-lg font-semibold text-red-600 mb-2">分析失败</h3>
          <p className="text-sm text-slate-500">{resume.summary || "未知错误"}</p>
          <button onClick={() => window.location.reload()} className="mt-4 text-blue-600 hover:underline text-sm">重试</button>
        </div>
      </div>
    );
  }

  if (_error) return (
    <div className="text-center py-12">
      <p className="text-red-500 mb-4">{_error}</p>
      <button onClick={() => window.location.reload()} className="text-blue-600 hover:underline">重试</button>
    </div>
  );

  return (
    <div>
      <Link to="/resumes" className="text-sm text-blue-600 hover:underline">&larr; 返回简历列表</Link>

      <div className="flex items-start justify-between mt-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">{resume.name || resume.filename}</h2>
          <p className="text-slate-500">{resume.position || "未知职位"}</p>
        </div>
        {resume.score != null && (
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{resume.score}</div>
            <div className="text-xs text-slate-400">综合评分</div>
          </div>
        )}
      </div>

      {resume.summary && (
        <div className="bg-white rounded-xl p-5 shadow-sm mb-4">
          <h3 className="font-semibold text-slate-800 mb-2">专业摘要</h3>
          <p className="text-sm text-slate-600">{resume.summary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-3">联系方式</h3>
          <p className="text-sm text-slate-600">邮箱：{resume.email || "未知"}</p>
          <p className="text-sm text-slate-600">电话：{resume.phone || "未知"}</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-3">技能</h3>
          <div className="flex flex-wrap gap-2">
            {resume.skills?.map((s) => (
              <span key={s} className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">{s}</span>
            )) || <span className="text-sm text-slate-400">无</span>}
          </div>
        </div>
      </div>

      {resume.experience && resume.experience.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm mb-4">
          <h3 className="font-semibold text-slate-800 mb-3">工作经历</h3>
          {resume.experience.map((exp, i) => (
            <div key={i} className="mb-3 pb-3 border-b border-slate-100 last:border-0">
              <p className="font-medium text-slate-800">{exp.title} @ {exp.company}</p>
              <p className="text-xs text-slate-400">{exp.duration}</p>
              <p className="text-sm text-slate-600 mt-1">{exp.description}</p>
            </div>
          ))}
        </div>
      )}

      {resume.education && resume.education.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-3">教育背景</h3>
          {resume.education.map((edu, i) => (
            <div key={i}>
              <p className="font-medium text-slate-800">{edu.school}</p>
              <p className="text-sm text-slate-600">{edu.degree} - {edu.major} ({edu.year})</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Step({ done, active, label }: { done?: boolean; active?: boolean; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${
        done ? "bg-green-500 text-white" :
        active ? "bg-blue-500 text-white animate-pulse" :
        "bg-slate-200 text-slate-400"
      }`}>
        {done ? "✓" : active ? "●" : "○"}
      </div>
      <span className={`text-sm ${done ? "text-green-600" : active ? "text-blue-600 font-medium" : "text-slate-400"}`}>
        {label}
      </span>
    </div>
  );
}
