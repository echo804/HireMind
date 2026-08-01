import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useToast } from "../contexts/ToastContext";
import ConfirmDialog from "../components/ConfirmDialog";

interface ResumeItem {
  id: string;
  name: string | null;
  position: string | null;
  filename: string;
}

interface InterviewItem {
  id: string; direction: string; interview_type: string;
  status: string; question_count: number; created_at: string;
}

const DIRECTION_OPTIONS = [
  { value: "frontend", label: "前端开发" },
  { value: "java", label: "Java 开发" },
  { value: "python", label: "Python 开发" },
  { value: "go", label: "Go 开发" },
  { value: "rust", label: "Rust 开发" },
  { value: "algorithm", label: "算法与数据结构" },
  { value: "ai_algorithm", label: "AI 算法工程师" },
  { value: "llm_engineer", label: "大模型应用开发" },
  { value: "nlp_engineer", label: "NLP 自然语言处理" },
  { value: "cv_engineer", label: "计算机视觉工程师" },
  { value: "data_science", label: "数据科学" },
  { value: "devops", label: "DevOps / SRE" },
  { value: "backend", label: "后端开发" },
  { value: "fullstack", label: "全栈开发" },
  { value: "product_manager", label: "产品经理" },
];

const STATUS_MAP: Record<string, string> = {
  pending: "待开始", in_progress: "进行中", completed: "已完成", cancelled: "已取消",
};

import { TableSkeleton } from "../components/Skeleton";

export default function InterviewList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [deleteTarget, setDeleteTarget] = useState<InterviewItem | null>(null);
  const [sessions, setSessions] = useState<InterviewItem[]>([]);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [direction, setDirection] = useState("frontend");
  const [resumeId, setResumeId] = useState("");
  const [totalQ, setTotalQ] = useState(5);
  const [useKnowledge, setUseKnowledge] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    try {
      const [sessionsData, resumesData] = await Promise.all([
        api.get<any>("/interviews"),
        api.get<any>("/resumes"),
      ]);
      setSessions(sessionsData || []);
      const list = (resumesData || []).filter((r: ResumeItem) => r.name);
      setResumes(list);
      if (list.length > 0) setResumeId(list[0].id);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === sessions.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(sessions.map(s => s.id)));
    }
  };

  const handleDelete = async (id: string) => {
    await api.delete("/interviews/" + id);
    setSelected(prev => { const n = new Set(prev); n.delete(id); return n; });
    toast("面试记录已删除", "success");
    await load();
  };

  const confirmDelete = () => {
    if (!deleteTarget) return;
    handleDelete(deleteTarget.id);
    setDeleteTarget(null);
  };

  const handleBatchDelete = async () => {
    if (selected.size === 0) return;
    await api.post("/interviews/batch-delete", { ids: Array.from(selected) });
    setSelected(new Set());
    await load();
  };

  const startInterview = async () => {
    setCreating(true);
    try {
      const data = await api.post<any>("/interviews", {
        resume_id: resumeId || null,
        direction,
        interview_type: "text",
        total_questions: totalQ,
        use_knowledge: useKnowledge,
      });
      if (data?.id) {
        navigate("/interviews/" + data.id);
      } else {
        toast("创建面试失败，请重试", "error");
      }
    } catch {
      toast("网络错误，请检查后端是否运行", "error");
    } finally { setCreating(false); }
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: "bg-gray-100 text-gray-600",
      in_progress: "bg-brand-100 text-brand-600",
      completed: "bg-green-100 text-green-600",
      cancelled: "bg-red-100 text-red-600",
    };
    return <span className={`text-xs px-2 py-0.5 rounded-full ${colors[status] || ""}`}>{STATUS_MAP[status] || status}</span>;
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-ink mb-6">模拟面试</h2>

      {/* New interview */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-8">
        <h3 className="font-semibold text-ink mb-4">新建面试</h3>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-sm text-ink-secondary mb-1">选择简历</label>
            <select value={resumeId} onChange={e => setResumeId(e.target.value)}
              className="px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[180px]">
              {resumes.length === 0 && <option value="">暂无简历</option>}
              {resumes.map(r => (
                <option key={r.id} value={r.id}>{r.name} - {r.position || "未知职位"}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-ink-secondary mb-1">面试方向</label>
            <select value={direction} onChange={e => setDirection(e.target.value)}
              className="px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 min-w-[160px]">
              {DIRECTION_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-ink-secondary mb-1">题目数量</label>
            <select value={totalQ} onChange={e => setTotalQ(Number(e.target.value))}
              className="px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
              {[3, 5, 8, 10].map(n => <option key={n} value={n}>{n} 道</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="useKnowledge" checked={useKnowledge}
              onChange={e => setUseKnowledge(e.target.checked)}
              className="w-4 h-4 rounded border-line text-brand-600 focus:ring-brand-500" />
            <label htmlFor="useKnowledge" className="text-sm text-ink-secondary cursor-pointer select-none">启用知识库出题</label>
          </div>
          <button onClick={startInterview} disabled={creating}
            className="px-6 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors">
            {creating ? "创建中..." : "开始面试"}
          </button>
        </div>
      </div>

      {/* Interview records */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-ink">面试记录</h3>
        {selected.size > 0 && (
          <button onClick={handleBatchDelete}
            className="text-sm text-red-500 hover:text-red-700">
            删除所选 ({selected.size})
          </button>
        )}
      </div>

      {loading ? (
        <TableSkeleton rows={4} />
      ) : sessions.length === 0 ? (
        <div className="text-center py-8 text-ink-muted">还没有面试记录</div>
      ) : (
        <div className="grid gap-3">
          {sessions.map(s => (
            <div key={s.id} className="bg-white rounded-xl p-4 shadow-sm flex items-center justify-between">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selected.has(s.id)}
                  onChange={() => toggleSelect(s.id)}
                  className="w-4 h-4 rounded border-line text-brand-600 focus:ring-brand-500"
                />
                <div>
                  <p className="font-medium text-ink">
                    {DIRECTION_OPTIONS.find(o => o.value === s.direction)?.label || s.direction}
                  </p>
                  <p className="text-sm text-ink-muted">
                    文字面试 &middot; {s.question_count} 题 &middot; {new Date(s.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {statusBadge(s.status)}
                {s.status === "in_progress" && (
                  <button onClick={() => navigate("/interviews/" + s.id)}
                    className="text-sm text-brand-600 hover:underline">继续</button>
                )}
                {s.status === "completed" && (
                  <button onClick={() => navigate("/interviews/" + s.id + "/report")}
                    className="text-sm text-brand-600 hover:underline">查看报告</button>
                )}
                <button onClick={() => setDeleteTarget(s)}
                  className="text-sm text-red-400 hover:text-red-600">删除</button>
              </div>
            </div>
          ))}
          {sessions.length > 0 && (
            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                checked={selected.size === sessions.length && sessions.length > 0}
                onChange={toggleAll}
                className="w-4 h-4 rounded border-line text-brand-600 focus:ring-brand-500"
              />
              <span className="text-xs text-ink-muted">全选</span>
            </div>
          )}
        </div>
      )}

      <ConfirmDialog
        open={deleteTarget !== null}
        title="删除面试记录"
        message={`确定要删除这场面试记录吗？删除后无法恢复。`}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}