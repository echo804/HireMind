import { useState, useEffect, useCallback, useRef } from "react";
import { useToast } from "../contexts/ToastContext";
import { api } from "../api/client";
import { Link } from "react-router-dom";

interface KBDoc {
  id: string;
  filename: string;
  file_type: string;
  category: string;
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
  chunk_id: string;
  document_id: string;
}

import { CardSkeleton } from "../components/Skeleton";
import { FileText, FileType2, File as FileIcon, UploadCloud, RefreshCw, Search as SearchIcon, Database, Layers, HardDrive, CheckCircle2, X } from "lucide-react";

const CATEGORIES: Record<string, string> = {
  agent: "AI Agent",
  llm: "大语言模型",
  rag: "RAG 知识库",
  tools: "工具与 MCP",
  overview: "综合概述",
  other: "其他",
};

// 高亮关键词
function Highlight({ text, keyword }: { text: string; keyword: string }) {
  if (!keyword.trim()) return <>{text}</>;
  const parts = text.split(new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi"));
  return (
    <>
      {parts.map((p, i) =>
        p.toLowerCase() === keyword.toLowerCase() ? (
          <mark key={i} className="bg-yellow-200 px-0.5 rounded">{p}</mark>
        ) : (
          <span key={i}>{p}</span>
        )
      )}
    </>
  );
}

export default function KnowledgeBase() {
  const { toast } = useToast();
  const [docs, setDocs] = useState<KBDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchedQuery, setSearchedQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [dragOver, setDragOver] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadDocs = useCallback(async () => {
    try {
      const data = await api.get<any>("/knowledge");
      setDocs(data || []);
    } catch {
      toast("加载文档失败", "error");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { loadDocs(); }, [loadDocs]);

  // 轮询 processing 状态，直到全部就绪/失败
  const startPolling = useCallback(async () => {
    if (pollingRef.current) return;
    const tick = async () => {
      const d = await api.get<any>("/knowledge");
      setDocs(d || []);
      const pending = (d || []).filter((x: KBDoc) => x.status === "processing");
      if (pending.length === 0) {
        if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      }
    };
    tick();
    pollingRef.current = setInterval(tick, 2000);
  }, []);

  useEffect(() => () => { if (pollingRef.current) clearInterval(pollingRef.current); }, []);

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    const names: string[] = [];
    try {
      for (const file of Array.from(files)) {
        names.push(file.name);
        const form = new FormData();
        form.append("file", file);
        await api.upload("/knowledge/upload", form);
      }
      toast(`已上传 ${files.length} 个文档，正在处理...`, "success");
      setUploadQueue(names);
      await loadDocs();
      startPolling();
    } catch (e: any) {
      toast(e.message || "上传失败", "error");
    } finally {
      setUploading(false);
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await api.post<any>(`/knowledge/${id}/retry`, {});
      toast("已重新处理", "success");
      startPolling();
    } catch (e: any) {
      toast(e.message || "重试失败", "error");
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
      const data = await api.post<any>("/knowledge/search", { query: searchQuery, top_k: 10 });
      setSearchResults(data || []);
      setSearchedQuery(searchQuery.trim());
    } catch {
      toast("搜索失败", "error");
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery("");
    setSearchedQuery("");
    setSearchResults([]);
  };

  // 输入变化时自动清空旧结果，避免展示过期内容
  const onSearchInputChange = (value: string) => {
    setSearchQuery(value);
    if (searchedQuery && value.trim() !== searchedQuery) {
      setSearchResults([]);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = { ready: "text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700", processing: "text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700", failed: "text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700", pending: "text-xs px-2 py-0.5 rounded-full bg-surface-muted text-ink-secondary" };
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

  // 统计
  const totalDocs = docs.length;
  const totalChunks = docs.reduce((s, d) => s + (d.chunk_count || 0), 0);
  const totalSize = docs.reduce((s, d) => s + (d.file_size || 0), 0);
  const readyCount = docs.filter(d => d.status === "ready").length;
  const readyRate = totalDocs ? Math.round((readyCount / totalDocs) * 100) : 0;

  // 搜索结果按文档分组
  const groupedResults = searchResults.reduce<Record<string, SearchResult[]>>((acc, r) => {
    (acc[r.document_name] = acc[r.document_name] || []).push(r);
    return acc;
  }, {});

  const visibleDocs = activeCategory === "all" ? docs : docs.filter(d => d.category === activeCategory);

  return (
    <div>
      {/* 顶部标题 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-ink">知识库</h2>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm p-4 flex items-center gap-3">
          <span className="w-10 h-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center"><Database className="w-5 h-5" strokeWidth={1.5} /></span>
          <div><p className="text-2xl font-bold text-ink">{totalDocs}</p><p className="text-xs text-ink-muted">文档总数</p></div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4 flex items-center gap-3">
          <span className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center"><Layers className="w-5 h-5" strokeWidth={1.5} /></span>
          <div><p className="text-2xl font-bold text-ink">{totalChunks}</p><p className="text-xs text-ink-muted">切片总数</p></div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4 flex items-center gap-3">
          <span className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center"><HardDrive className="w-5 h-5" strokeWidth={1.5} /></span>
          <div><p className="text-2xl font-bold text-ink">{formatSize(totalSize)}</p><p className="text-xs text-ink-muted">总大小</p></div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4 flex items-center gap-3">
          <span className="w-10 h-10 rounded-lg bg-green-50 text-green-600 flex items-center justify-center"><CheckCircle2 className="w-5 h-5" strokeWidth={1.5} /></span>
          <div><p className="text-2xl font-bold text-ink">{readyRate}%</p><p className="text-xs text-ink-muted">就绪率（{readyCount}/{totalDocs}）</p></div>
        </div>
      </div>

      {/* 上传区（拖拽） */}
      <div
        className={`mb-6 rounded-xl border-2 border-dashed p-8 text-center transition-colors ${dragOver ? "border-brand-500 bg-brand-50" : "border-line bg-white"}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files); }}
      >
        <UploadCloud className="w-8 h-8 mx-auto mb-2 text-brand-500" strokeWidth={1.5} />
        <p className="text-sm text-ink-secondary mb-1">{uploading ? "上传中..." : "拖拽文档到此处，或点击选择文件"}</p>
        <p className="text-xs text-ink-muted mb-3">支持 PDF / DOCX / TXT / Markdown，可多选</p>
        <label className="inline-block px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 cursor-pointer transition-colors">
          选择文件
          <input type="file" multiple accept=".pdf,.docx,.txt,.md" onChange={(e) => { handleUpload(e.target.files); e.target.value = ""; }} className="hidden" disabled={uploading} />
        </label>
        {uploadQueue.length > 0 && (
          <p className="text-xs text-brand-600 mt-2">正在后台处理：{uploadQueue.join("、")}，处理完成自动刷新</p>
        )}
      </div>

      {/* 搜索 */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
            <input value={searchQuery} onChange={(e) => onSearchInputChange(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="搜索知识库内容（语义检索）..."
              className="w-full pl-9 pr-8 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
            {searchQuery && (
              <button onClick={clearSearch} title="清空搜索"
                className="absolute right-2.5 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded-full bg-surface-muted text-ink-muted hover:bg-line hover:text-ink transition-colors">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
          <button onClick={handleSearch} disabled={searching || !searchQuery.trim()}
            className="px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors">
            {searching ? "搜索中..." : "搜索"}
          </button>
        </div>
        {Object.keys(groupedResults).length > 0 && (
          <div className="mt-4 space-y-4 border-t border-line pt-4">
            <p className="text-sm font-medium text-ink">搜索结果（按文档分组）</p>
            {Object.entries(groupedResults).map(([docName, results]) => (
              <div key={docName} className="bg-surface-muted rounded-lg p-3">
                <p className="text-xs font-medium text-brand-600 mb-2">📄 {docName}</p>
                <div className="space-y-2">
                  {results.map((r, i) => (
                    <div key={i} className="bg-white rounded-lg p-3 border border-line">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-ink-muted">片段 {r.chunk_index + 1}</span>
                        <span className="text-xs text-ink-muted">匹配度 {(r.score * 100).toFixed(0)}%</span>
                      </div>
                      <p className="text-sm text-ink"><Highlight text={r.content} keyword={searchQuery} /></p>
                      <Link to={`/knowledge-base/${r.document_id}?chunk=${r.chunk_index}`}
                        className="inline-block mt-2 text-xs text-brand-500 hover:underline">
                        查看原文定位 →
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        {searching && <p className="text-xs text-ink-muted mt-3">正在检索...</p>}
      </div>

      {/* 分类 tabs */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button onClick={() => setActiveCategory("all")}
          className={activeCategory === "all" ? "px-3 py-1.5 text-sm font-medium rounded-lg bg-brand-600 text-white" : "px-3 py-1.5 text-sm font-medium rounded-lg bg-white text-ink-secondary hover:bg-surface-muted border border-line"}>
          全部 ({docs.length})
        </button>
        {Object.entries(CATEGORIES).map(([key, label]) => {
          const count = docs.filter(d => d.category === key).length;
          if (count === 0 && key !== "other") return null;
          return (
            <button key={key} onClick={() => setActiveCategory(key)}
              className={activeCategory === key ? "px-3 py-1.5 text-sm font-medium rounded-lg bg-brand-600 text-white" : "px-3 py-1.5 text-sm font-medium rounded-lg bg-white text-ink-secondary hover:bg-surface-muted border border-line"}>
              {label} ({count})
            </button>
          );
        })}
      </div>

      {/* 文档列表 */}
      {loading ? (
        <CardSkeleton count={3} />
      ) : docs.length === 0 ? (
        <div className="text-center py-12 text-ink-muted bg-white rounded-xl shadow-sm">
          <p className="mb-2">暂无文档</p>
          <p className="text-sm">拖拽或点击上方区域上传资料</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {visibleDocs.map((doc) => (
            <div key={doc.id} className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <span className="shrink-0 text-ink-muted">
                  {doc.file_type === "pdf" ? <FileText className="w-5 h-5" strokeWidth={1.5} /> : doc.file_type === "docx" ? <FileType2 className="w-5 h-5" strokeWidth={1.5} /> : <FileIcon className="w-5 h-5" strokeWidth={1.5} />}
                </span>
                <div className="min-w-0">
                  <p className="font-medium text-ink truncate">{doc.filename}</p>
                  <p className="text-xs text-ink-muted">{formatSize(doc.file_size)} · {doc.chunk_count} 个切片{doc.created_at && ` · ${new Date(doc.created_at).toLocaleDateString("zh-CN")}`}{doc.category !== "other" && ` · ${CATEGORIES[doc.category] || doc.category}`}</p>
                  {doc.status === "failed" && doc.error_message && (
                    <p className="text-xs text-red-500 truncate mt-0.5">{doc.error_message.slice(0, 80)}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {statusBadge(doc.status)}
                {doc.status === "failed" && (
                  <button onClick={() => handleRetry(doc.id)} className="text-xs text-brand-500 hover:underline flex items-center gap-1">
                    <RefreshCw className="w-3 h-3" /> 重试
                  </button>
                )}
                <Link to={"/knowledge-base/" + doc.id} className="text-xs text-brand-500 hover:underline">查看</Link>
                <button onClick={() => setDeleteTarget(doc.id)} className="text-xs text-red-400 hover:text-red-600">删除</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {deleteTarget !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h3 className="text-lg font-semibold text-ink mb-2">确认删除</h3>
            <p className="text-sm text-ink-secondary mb-6">确定要删除该文档吗？关联的切片数据也将被删除。</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)} disabled={deleting}
                className="px-4 py-2 text-sm text-ink-secondary bg-surface-muted rounded-lg hover:bg-surface-muted disabled:opacity-50 transition-colors">
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
