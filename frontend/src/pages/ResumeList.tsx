import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import { api } from "../api/client";

interface ResumeItem {
  id: string;
  filename: string;
  name: string | null;
  position: string | null;
  score: number | null;
  status: string;
  created_at: string;
}

import { CardSkeleton } from "../components/Skeleton";

export default function ResumeList() {
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const loadResumes = useCallback(async (query?: string) => {
    try {
      const path = query ? `/resumes?q=${encodeURIComponent(query)}` : "/resumes";
      const data = await api.get<any>(path);
      setResumes(data || []);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadResumes(search); }, [loadResumes, search]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      await api.upload("/resumes/upload", form);
      await loadResumes();
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    await api.delete("/resumes/" + deleteId);
    setDeleteId(null);
    await loadResumes();
  };

  const statusBadge = (status: string, score: number | null) => {
    if (status === "done") {
      const label = score !== null ? String(score) : "?";
      if (score && score >= 80) {
        return <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">{label}</span>;
      } else if (score && score >= 60) {
        return <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">{label}</span>;
      } else {
        return <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">{label}</span>;
      }
    }
    if (status === "failed") return <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">解析失败</span>;
    return <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">处理中</span>;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800">简历管理</h2>
        <div className="flex items-center gap-3">
          <input
            type="text" placeholder="搜索姓名/职位..." value={search}
            onChange={e => setSearch(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <label className="cursor-pointer px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
            {uploading ? "上传中..." : "上传简历"}
            <input type="file" accept=".pdf,.docx" onChange={handleUpload} className="hidden" disabled={uploading} />
          </label>
        </div>
      </div>

      {loading ? (
        <CardSkeleton count={3} />
      ) : resumes.length === 0 ? (
        <div className="text-center py-12 text-slate-400">还没有简历，点击上传按钮开始</div>
      ) : (
        <div className="grid gap-4">
          {resumes.map((r) => (
            <div key={r.id} className="bg-white rounded-xl p-5 shadow-sm flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                  {r.name?.[0] || "?"}
                </div>
                <div>
                  <Link to={"/resumes/" + r.id} className="font-medium text-slate-800 hover:text-blue-600">
                    {r.name || r.filename}
                  </Link>
                  <p className="text-sm text-slate-400">
                    {r.position || "未知职位"} &middot; {new Date(r.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {statusBadge(r.status, r.score)}
                <button onClick={() => setDeleteId(r.id)} className="text-sm text-red-400 hover:text-red-600">删除</button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteId}
        title="删除简历"
        message="确定要删除这份简历吗？此操作不可撤销。"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
