import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { DetailSkeleton } from "../components/Skeleton";

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
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [_error, setError] = useState<string | null>(null);
  const [_pollCount, setPollCount] = useState(0);
  const [duplicate, setDuplicate] = useState<{ duplicate_of: string; duplicate_filename: string } | null>(null);
  // 编辑表单
  const [form, setForm] = useState({
    name: "", position: "", email: "", phone: "",
    skills: "", summary: "",
  });

  const startEdit = () => {
    if (!resume) return;
    setForm({
      name: resume.name || "",
      position: resume.position || "",
      email: resume.email || "",
      phone: resume.phone || "",
      skills: (resume.skills || []).join(", "),
      summary: resume.summary || "",
    });
    setEditing(true);
  };

  const saveEdit = async () => {
    if (!resume) return;
    setSaving(true);
    try {
      const data = await api.put<any>("/resumes/" + resume.id, {
        name: form.name || null,
        position: form.position || null,
        email: form.email || null,
        phone: form.phone || null,
        skills: form.skills.split(/[,，]/).map(s => s.trim()).filter(Boolean),
        summary: form.summary || null,
      });
      setResume(data);
      setEditing(false);
    } catch {
      setError("保存失败，请重试");
    } finally {
      setSaving(false);
    }
  };

  useEffect(function poll() {
    api.get<any>("/resumes/" + id).then(data => {
      setResume(data);
      if (data.status === "done" || data.status === "failed") {
        setLoading(false);
        // 解析完成后检测重复
        if (data.status === "done") {
          api.get<any>(`/resumes/${id}/duplicate`).then(dup => {
            if (dup) setDuplicate(dup);
          }).catch(() => { /* ignore */ });
        }
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
        <Link to="/resumes" className="text-sm text-brand-600 hover:underline">&larr; 返回简历列表</Link>
        <div className="mt-4">
          <DetailSkeleton />
          <p className="text-center text-ink-muted text-sm mt-4">正在分析简历...</p>
        </div>
      </div>
    );
  }

  if (!resume) return <div className="text-center py-12 text-ink-muted">简历不存在</div>;

  if (resume.status === "processing") {
    const pct = resume.progress || 0;
    const stepLabel = pct < 20 ? "解析 PDF 文本..." :
      pct < 50 ? "AI 智能分析中..." :
      pct < 80 ? "正在提取关键信息..." :
      "正在生成报告...";
    return (
      <div>
        <Link to="/resumes" className="text-sm text-brand-600 hover:underline">&larr; 返回简历列表</Link>
        <div className="text-center py-16">
          <h3 className="text-lg font-semibold text-ink mb-2">AI 正在分析简历</h3>
          <p className="text-sm text-ink-muted mb-6">{stepLabel}</p>
          {/* 百分比进度条 */}
          <div className="max-w-md mx-auto mb-3">
            <div className="flex justify-between text-xs text-ink-muted mb-1">
              <span>进度</span><span>{pct}%</span>
            </div>
            <div className="w-full bg-surface-muted rounded-full h-3 overflow-hidden">
              <div className="bg-brand-600 h-3 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${pct}%` }} />
            </div>
          </div>
          {/* 步骤指示器 */}
          <div className="max-w-sm mx-auto space-y-2 mt-6">
            <Step done={pct >= 20} active={pct < 20} label="解析 PDF 文本" />
            <Step done={pct >= 90} active={pct >= 20 && pct < 90} label="AI 智能分析" />
            <Step done={pct === 100} active={pct >= 90 && pct < 100} label="生成报告" />
          </div>
          <p className="text-xs text-ink-muted mt-6">通常需要 10-30 秒，请稍候...</p>
        </div>
      </div>
    );
  }

  if (resume.status === "failed") {
    return (
      <div>
        <Link to="/resumes" className="text-sm text-brand-600 hover:underline">&larr; 返回简历列表</Link>
        <div className="text-center py-16">
          <div className="text-4xl mb-4">&#10060;</div>
          <h3 className="text-lg font-semibold text-red-600 mb-2">分析失败</h3>
          <p className="text-sm text-ink-secondary">{resume.summary || "未知错误"}</p>
          <button onClick={() => window.location.reload()} className="mt-4 text-brand-600 hover:underline text-sm">重试</button>
        </div>
      </div>
    );
  }

  if (_error) return (
    <div className="text-center py-12">
      <p className="text-red-500 mb-4">{_error}</p>
      <button onClick={() => window.location.reload()} className="text-brand-600 hover:underline">重试</button>
    </div>
  );

  return (
    <div>
      <Link to="/resumes" className="text-sm text-brand-600 hover:underline">&larr; 返回简历列表</Link>

      {duplicate && (
        <div className="mt-4 flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4">
          <span className="text-amber-500 text-lg">&#9888;&#65039;</span>
          <div>
            <p className="text-sm font-medium text-amber-700">检测到重复简历</p>
            <p className="text-sm text-amber-600 mt-1">
              这份简历与已存在的
              <Link to={"/resumes/" + duplicate.duplicate_of} className="text-amber-700 underline mx-1">
                {duplicate.duplicate_filename}
              </Link>
              内容相同，可能重复上传。
            </p>
          </div>
        </div>
      )}

      <div className="flex items-start justify-between mt-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-ink">{resume.name || resume.filename}</h2>
          <p className="text-ink-secondary">{resume.position || "未知职位"}</p>
        </div>
        <div className="flex items-center gap-3">
          {resume.score != null && (
            <div className="text-center mr-2">
              <div className="text-3xl font-bold text-brand-600">{resume.score}</div>
              <div className="text-xs text-ink-muted">综合评分</div>
            </div>
          )}
          {!editing ? (
            <button onClick={startEdit} className="px-4 py-2 text-sm text-white bg-brand-600 rounded-lg hover:bg-brand-700 transition-colors">
              编辑信息
            </button>
          ) : (
            <div className="flex gap-2">
              <button onClick={() => setEditing(false)} disabled={saving}
                className="px-4 py-2 text-sm text-ink-secondary bg-surface-muted rounded-lg hover:bg-surface-muted transition-colors">
                取消
              </button>
              <button onClick={saveEdit} disabled={saving}
                className="px-4 py-2 text-sm text-white bg-brand-600 rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors">
                {saving ? "保存中..." : "保存修改"}
              </button>
            </div>
          )}
        </div>
      </div>

      {editing ? (
        <div className="bg-white rounded-xl p-5 shadow-sm mb-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-ink-muted mb-1">姓名</label>
              <input className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">职位</label>
              <input className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={form.position} onChange={e => setForm({ ...form, position: e.target.value })} />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">邮箱</label>
              <input className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">电话</label>
              <input className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="block text-xs text-ink-muted mb-1">技能（逗号分隔）</label>
            <input className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.skills} onChange={e => setForm({ ...form, skills: e.target.value })} placeholder="React, TypeScript, FastAPI" />
          </div>
          <div>
            <label className="block text-xs text-ink-muted mb-1">专业摘要</label>
            <textarea rows={3} className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.summary} onChange={e => setForm({ ...form, summary: e.target.value })} />
          </div>
        </div>
      ) : (
        <>
      {resume.summary && (
        <div className="bg-white rounded-xl p-5 shadow-sm mb-4">
          <h3 className="font-semibold text-ink mb-2">专业摘要</h3>
          <p className="text-sm text-ink-secondary">{resume.summary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-ink mb-3">联系方式</h3>
          <p className="text-sm text-ink-secondary">邮箱：{resume.email || "未知"}</p>
          <p className="text-sm text-ink-secondary">电话：{resume.phone || "未知"}</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-ink mb-3">技能</h3>
          <div className="flex flex-wrap gap-2">
            {resume.skills?.map((s) => (
              <span key={s} className="text-xs px-2 py-1 rounded-full bg-brand-100 text-brand-700">{s}</span>
            )) || <span className="text-sm text-ink-muted">无</span>}
          </div>
        </div>
      </div>
        </>
      )}

      {resume.experience && resume.experience.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm mb-4">
          <h3 className="font-semibold text-ink mb-3">工作经历</h3>
          {resume.experience.map((exp, i) => (
            <div key={i} className="mb-3 pb-3 border-b border-line last:border-0">
              <p className="font-medium text-ink">{exp.title} @ {exp.company}</p>
              <p className="text-xs text-ink-muted">{exp.duration}</p>
              <p className="text-sm text-ink-secondary mt-1">{exp.description}</p>
            </div>
          ))}
        </div>
      )}

      {resume.education && resume.education.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-ink mb-3">教育背景</h3>
          {resume.education.map((edu, i) => (
            <div key={i}>
              <p className="font-medium text-ink">{edu.school}</p>
              <p className="text-sm text-ink-secondary">{edu.degree} - {edu.major} ({edu.year})</p>
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
        active ? "bg-brand-500 text-white animate-pulse" :
        "bg-surface-muted text-ink-muted"
      }`}>
        {done ? "✓" : active ? "●" : "○"}
      </div>
      <span className={`text-sm ${done ? "text-green-600" : active ? "text-brand-600 font-medium" : "text-ink-muted"}`}>
        {label}
      </span>
    </div>
  );
}
