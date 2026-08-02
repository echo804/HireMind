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
  // AI 诊断与润色
  const [analyzing, setAnalyzing] = useState(false);
  const [polishing, setPolishing] = useState(false);
  const [diagnosis, setDiagnosis] = useState<any>(null);
  const [polishResult, setPolishResult] = useState<any>(null);
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

  const handleAnalyze = async () => {
    if (!resume || analyzing) return;
    setAnalyzing(true);
    try {
      const data = await api.post<any>(`/resumes/${resume.id}/analyze`);
      setDiagnosis(data);
    } catch {
      setDiagnosis({ overall_score: 0, verdict: "分析失败，请检查 AI 配置后重试", dimensions: [], highlights: [], red_flags: [], llm_extra: false });
    } finally {
      setAnalyzing(false);
    }
  };

  const handlePolish = async () => {
    if (!resume || polishing) return;
    setPolishing(true);
    try {
      const data = await api.post<any>(`/resumes/${resume.id}/polish`);
      setPolishResult(data);
    } catch {
      setPolishResult({ polished_text: "", changes: [], summary: "润色失败，请检查 AI 配置后重试" });
    } finally {
      setPolishing(false);
    }
  };

  const handleExport = async () => {
    if (!resume || !polishResult?.polished_text) return;
    try {
      const blob = await api.postBlob(`/resumes/${resume.id}/export`, { polished_text: polishResult.polished_text });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const name = (resume.name || "resume").replace(/\s+/g, "_");
      a.href = url;
      a.download = `${name}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("导出失败，请重试");
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

      {/* AI 诊断与润色 */}
      <div className="bg-white rounded-xl p-5 shadow-sm mt-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-ink">AI 简历诊断与润色</h3>
          <div className="flex gap-2">
            <button onClick={handlePolish} disabled={polishing || analyzing}
              className="px-4 py-2 text-sm text-white bg-violet-600 rounded-lg hover:bg-violet-700 disabled:opacity-50 transition-colors">
              {polishing ? "润色中..." : "✨ AI 润色"}
            </button>
            <button onClick={handleAnalyze} disabled={analyzing || polishing}
              className="px-4 py-2 text-sm text-white bg-brand-600 rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors">
              {analyzing ? "分析中..." : "🔍 AI 诊断"}
            </button>
          </div>
        </div>

        {diagnosis && (
          <div className="border-t border-line pt-5 mt-1">
            {/* 总览卡片 */}
            <div className="bg-gradient-to-br from-brand-50 to-white border border-brand-100 rounded-2xl p-5 mb-5 flex items-center gap-5">
              <RingScore score={diagnosis.overall_score || 0} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  {(() => {
                    const g = GRADE_MAP.find(g => (diagnosis.overall_score || 0) >= g.min) || GRADE_MAP[2];
                    return <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${g.cls}`}>{g.label}</span>;
                  })()}
                  {diagnosis.llm_extra && (
                    <span className="text-xs px-2.5 py-1 rounded-full bg-purple-100 text-purple-700 font-medium">含大模型岗加试</span>
                  )}
                </div>
                <p className="text-sm text-ink leading-relaxed">{diagnosis.verdict || "综合评估"}</p>
                <div className="flex gap-4 mt-2 text-xs text-ink-muted flex-wrap">
                  <span>📊 {(diagnosis.dimensions || []).length} 个维度</span>
                  <span>⭐ {(diagnosis.highlights || []).length} 处高亮</span>
                  <span className={((diagnosis.red_flags || []).length > 0 ? "text-red-500" : "")}>
                    🚩 {(diagnosis.red_flags || []).length} 条红线
                  </span>
                </div>
              </div>
            </div>

            {/* 维度分组 */}
            {["general", "llm"].map(group => {
              const dims = (diagnosis.dimensions || []).filter((d: any) => dimensionGroup(d) === group);
              if (dims.length === 0) return null;
              const avg = Math.round(dims.reduce((s: number, d: any) => s + (d.score || 0), 0) / dims.length);
              return (
                <div key={group} className="mb-5">
                  <div className="flex items-center justify-between mb-2.5">
                    <h4 className="text-sm font-semibold text-ink">{groupNames[group]}</h4>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${scoreBadgeCls(avg)}`}>
                      组均分 {avg}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {dims.map((d: any) => {
                      const passed = (d.score || 0) >= 70;
                      return (
                        <details key={d.key} className="group bg-white border border-line rounded-xl overflow-hidden" open={!passed}>
                          <summary className="flex items-center gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${
                              passed ? "bg-green-100 text-green-600" : "bg-red-100 text-red-500"
                            }`}>
                              {passed ? "✓" : "!"}
                            </span>
                            <span className="flex-1 text-sm font-medium text-ink">{d.name}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${scoreBadgeCls(d.score || 0)}`}>
                              {d.score}/100
                            </span>
                            <svg className={`w-4 h-4 text-ink-muted transition-transform group-open:rotate-180`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </summary>
                          <div className="px-4 pb-4">
                            <div className="w-full bg-surface-muted rounded-full h-1.5 mb-3 overflow-hidden">
                              <div className={`h-1.5 rounded-full ${barCls(d.score || 0)}`} style={{ width: `${Math.min(100, d.score || 0)}%` }} />
                            </div>
                            {(d.issues || []).length > 0 && (
                              <div className="mb-3">
                                <p className="text-xs font-medium text-red-600 mb-1">存在的问题</p>
                                <ul className="space-y-1">
                                  {d.issues.map((issue: string, i: number) => (
                                    <li key={i} className="flex gap-2 text-xs text-ink-secondary leading-relaxed">
                                      <span className="text-red-400 shrink-0">•</span>{issue}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {(d.suggestions || []).length > 0 && (
                              <div>
                                <p className="text-xs font-medium text-brand-600 mb-1">改进建议</p>
                                <ul className="space-y-1">
                                  {d.suggestions.map((s: string, i: number) => (
                                    <li key={i} className="flex gap-2 text-xs text-ink-secondary leading-relaxed">
                                      <span className="text-brand-400 shrink-0">→</span>{s}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </details>
                      );
                    })}
                  </div>
                </div>
              );
            })}

            {/* 红线与高亮 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(diagnosis.red_flags || []).length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                  <p className="text-sm font-semibold text-red-700 mb-2">🚩 淘汰红线</p>
                  <ul className="space-y-1.5">
                    {diagnosis.red_flags.map((f: string, i: number) => (
                      <li key={i} className="flex gap-2 text-xs text-red-600 leading-relaxed">
                        <span className="shrink-0">•</span>{f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {(diagnosis.highlights || []).length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                  <p className="text-sm font-semibold text-green-700 mb-2">⭐ 高亮时刻</p>
                  <ul className="space-y-1.5">
                    {diagnosis.highlights.map((h: string, i: number) => (
                      <li key={i} className="flex gap-2 text-xs text-green-700 leading-relaxed">
                        <span className="shrink-0">•</span>{h}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* 不合理之处建议 */}
            {(diagnosis.unreasonable_advice || []).length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-4">
                <p className="text-sm font-semibold text-amber-700 mb-2">⚠️ 不合理之处与建议</p>
                <div className="space-y-3">
                  {(diagnosis.unreasonable_advice || []).map((u: any, i: number) => (
                    <div key={i} className="text-xs">
                      <p className="text-amber-800 font-medium">• {u.issue}</p>
                      <p className="text-amber-700 mt-0.5 pl-4">→ 建议：{u.advice}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 项目真实性评估 */}
            {(diagnosis.project_assessment || []).length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-semibold text-ink mb-2.5">🔍 项目真实性评估</p>
                <div className="space-y-2">
                  {(diagnosis.project_assessment || []).map((pj: any, i: number) => (
                    <div key={i} className="bg-white border border-line rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-medium text-ink">{pj.name}</p>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            pj.type === "production" ? "bg-green-100 text-green-700" :
                            pj.type === "course" ? "bg-blue-100 text-blue-700" :
                            "bg-red-100 text-red-700"
                          }`}>
                            {pj.type === "production" ? "真实生产" : pj.type === "course" ? "课程项目" : "Demo 项目"}
                          </span>
                          <span className="text-xs text-ink-muted">{pj.confidence}%</span>
                        </div>
                      </div>
                      {(pj.reasons || []).length > 0 && (
                        <ul className="mb-2 space-y-0.5">
                          {pj.reasons.map((r: string, j: number) => (
                            <li key={j} className="flex gap-2 text-xs text-ink-secondary leading-relaxed">
                              <span className="text-ink-muted shrink-0">•</span>{r}
                            </li>
                          ))}
                        </ul>
                      )}
                      {pj.advice && (
                        <p className="text-xs text-brand-600 bg-brand-50 rounded-lg p-2">
                          → 建议：{pj.advice}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {polishResult && (
          <div className="border-t border-line pt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-ink">润色结果</h4>
              <div className="flex gap-2">
                <button onClick={handleExport} disabled={!polishResult?.polished_text}
                  className="px-4 py-2 text-sm text-white bg-brand-600 rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors">
                  📄 导出 .docx
                </button>
              </div>
            </div>
            {polishResult.summary && (
              <p className="text-xs text-ink-muted mb-3">{polishResult.summary}</p>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-surface-muted rounded-lg p-3">
                <p className="text-xs text-ink-muted mb-2">原文</p>
                <p className="text-xs text-ink-secondary whitespace-pre-wrap max-h-64 overflow-y-auto">{polishResult.original || resume.summary || ""}</p>
              </div>
              <div className="bg-brand-50 rounded-lg p-3">
                <p className="text-xs text-brand-600 mb-2">润色后</p>
                <p className="text-xs text-ink-secondary whitespace-pre-wrap max-h-64 overflow-y-auto">{polishResult.polished_text}</p>
              </div>
            </div>
            {(polishResult.changes || []).length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-ink-muted mb-2">主要变更（{polishResult.changes.length} 处）</p>
                {(polishResult.changes || []).slice(0, 5).map((c: any, i: number) => (
                  <div key={i} className="text-xs text-ink-secondary mb-2 bg-surface-muted rounded p-2">
                    <p><span className="text-red-500 line-through">{c.original}</span> → <span className="text-green-600">{c.polished}</span></p>
                    <p className="text-ink-muted mt-0.5">{c.reason}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
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

/* ===== AI 诊断展示组件 ===== */

function RingScore({ score }: { score: number }) {
  const color = score >= 80 ? "#16a34a" : score >= 60 ? "#ca8a04" : "#dc2626";
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;
  return (
    <div className="relative w-28 h-28 shrink-0">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
        <circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold" style={{ color }}>{score}</span>
        <span className="text-[10px] text-ink-muted">综合得分</span>
      </div>
    </div>
  );
}

const GRADE_MAP = [
  { min: 80, label: "优秀", cls: "bg-green-100 text-green-700" },
  { min: 60, label: "良好", cls: "bg-amber-100 text-amber-700" },
  { min: 0, label: "待改进", cls: "bg-red-100 text-red-700" },
];

const dimensionGroup = (d: any) =>
  (d.key || "").startsWith("llm_") ? "llm" : "general";

const groupNames: Record<string, string> = {
  general: "通用评审（面试官铁律）",
  llm: "大模型岗加试",
};

function scoreBadgeCls(score: number) {
  if (score >= 70) return "bg-green-100 text-green-700";
  if (score >= 50) return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-700";
}
function barCls(score: number) {
  if (score >= 70) return "bg-green-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-red-500";
}
