import { useState, useEffect } from "react";
import { useToast } from "../contexts/ToastContext";
import { api } from "../api/client";
import { Link } from "react-router-dom";

interface KBDoc {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  chunk_count: number;
  error_message: string | null;
  created_at: string | null;
}

interface SearchResult {
  content: string;
  document_name: string;
  score: number;
  chunk_index: number;
}

import { CardSkeleton } from "../components/Skeleton";

export default function KnowledgeBase() {
  const { toast } = useToast();
  const [docs, setDocs] = useState<KBDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>("all");

  const CATEGORIES: Record<string, string> = {
    agent: "AI Agent",
    llm: "大语言模型",
    rag: "RAG 知识库",
    tools: "工具与 MCP",
    overview: "综合概述",
  };

  const getCategory = (filename: string): string => {
    const prefix = filename.split("_")[0];
    return CATEGORIES[prefix] ? prefix : "other";
  };

  const loadDocs = async () => {
    try {
      const data = await api.get<any>("/knowledge");
      setDocs(data || []);
    } catch {
      toast("加载文档失败", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDocs(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      await api.upload("/knowledge/upload", form);
      toast("上传成功", "success");
      await loadDocs();
    } catch (e: any) {
      toast(e.message || "上传失败", "error");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete("/knowledge/" + id);
      toast("文档已删除", "success");
      await loadDocs();
    } catch (e: any) {
      toast(e.message || "删除失败", "error");
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await api.post<any>("/knowledge/search", { query: searchQuery, top_k: 5 });
      setSearchResults(data || []);
    } catch {
      toast("搜索失败", "error");
    } finally {
      setSearching(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = { ready: "text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700", processing: "text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700", failed: "text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700", pending: "text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600" };
    const labels: Record<string, string> = { ready: "已完成", processing: "处理中", failed: "失败", pending: "待处理" };
    return <span className={styles[status] || styles.pending}>{labels[status] || status}</span>;
  };

  const confirmDelete = async () => {
    if (deleteTarget === null) return;
    setDeleting(true);
    await handleDelete(deleteTarget);
    setDeleting(false);
    setDeleteTarget(null);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800">知识库</h2>
        <label className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 cursor-pointer transition-colors">
          {uploading ? "上传中..." : "上传文档"}
          <input type="file" multiple accept=".pdf,.docx,.txt,.md" onChange={handleUpload} className="hidden" disabled={uploading} />
        </label>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex gap-3">
          <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="搜索知识库内容..."
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button onClick={handleSearch} disabled={searching || !searchQuery.trim()}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {searching ? "搜索中..." : "搜索"}
          </button>
        </div>
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
            <p className="text-sm font-medium text-slate-700">搜索结果</p>
            {searchResults.map((r, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-slate-400">{r.document_name}</span>
                  <span className="text-xs text-slate-400">匹配度 {(r.score * 100).toFixed(0)}%</span>
                </div>
                <p className="text-sm text-slate-700">{r.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button onClick={() => setActiveCategory("all")}
          className={activeCategory === "all" ? "px-3 py-1.5 text-sm font-medium rounded-lg bg-blue-600 text-white" : "px-3 py-1.5 text-sm font-medium rounded-lg bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"}>
          全部 ({docs.length})
        </button>
        {Object.entries(CATEGORIES).map(([key, label]) => {
          const count = docs.filter(d => getCategory(d.filename) === key).length;
          if (count === 0) return null;
          return (
            <button key={key} onClick={() => setActiveCategory(key)}
              className={activeCategory === key ? "px-3 py-1.5 text-sm font-medium rounded-lg bg-blue-600 text-white" : "px-3 py-1.5 text-sm font-medium rounded-lg bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"}>
              {label} ({count})
            </button>
          );
        })}
      </div>

      {/* Doc list */}
      {loading ? (
        <CardSkeleton count={3} />
      ) : docs.length === 0 ? (
        <div className="text-center py-12 text-slate-400 bg-white rounded-xl shadow-sm">
          <p className="mb-2">暂无文档</p>
          <p className="text-sm">点击上方"上传文档"按钮添加资料</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {(activeCategory === "all"
            ? docs
            : docs.filter(d => getCategory(d.filename) === activeCategory)
          ).map((doc) => (
            <div key={doc.id} className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-2xl shrink-0">{doc.file_type === "pdf" ? "📫" : doc.file_type === "docx" ? "📑" : "📩"}</span>
                <div className="min-w-0">
                  <p className="font-medium text-slate-800 truncate">{doc.filename}</p>
                  <p className="text-xs text-slate-400">{formatSize(doc.file_size)} · {doc.chunk_count} 个切片{doc.created_at && ` · ${new Date(doc.created_at).toLocaleDateString("zh-CN")}`}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {statusBadge(doc.status)}
                <Link to={"/knowledge-base/" + doc.id} className="text-xs text-blue-500 hover:underline">查看</Link>
                <button onClick={() => setDeleteTarget(doc.id)} className="text-xs text-red-400 hover:text-red-600">删除</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {deleteTarget !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">确认删除</h3>
            <p className="text-sm text-slate-500 mb-6">确定要删除该文档吗？关联的切片数据也将被删除。</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)} disabled={deleting}
                className="px-4 py-2 text-sm text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 disabled:opacity-50 transition-colors">
                取消
              </button>
              <button onClick={confirmDelete} disabled={deleting}
                className="px-4 py-2 text-sm text-white bg-red-500 rounded-lg hover:bg-red-600 disabled:opacity-50 transition-colors">
                {deleting ? "删除中..." : "确定删除"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
