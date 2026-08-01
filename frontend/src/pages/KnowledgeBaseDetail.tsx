import { useState, useEffect, useMemo, useRef } from "react";
import { useParams, Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useToast } from "../contexts/ToastContext";
import { DetailSkeleton } from "../components/Skeleton";
import { Search as SearchIcon, Copy, Check } from "lucide-react";

interface DocContent {
  id: string;
  filename: string;
  chunks: { index: number; content: string }[];
}

export default function KnowledgeBaseDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const [doc, setDoc] = useState<DocContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [copied, setCopied] = useState<number | null>(null);
  const targetChunk = searchParams.get("chunk");
  const highlightRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get<any>(`/knowledge/${id}/content`);
        setDoc(data);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  // 定位到目标切片
  useEffect(() => {
    if (targetChunk && !loading && doc) {
      setTimeout(() => {
        const el = document.getElementById(`chunk-${targetChunk}`);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          el.classList.add("ring-2", "ring-brand-400");
          setTimeout(() => el.classList.remove("ring-2", "ring-brand-400"), 3000);
        }
      }, 300);
    }
  }, [loading, doc, targetChunk]);

  const copyChunk = async (index: number, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(index);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      toast("复制失败", "error");
    }
  };

  const visibleChunks = useMemo(() => {
    if (!doc) return [];
    if (!filter.trim()) return doc.chunks;
    const kw = filter.toLowerCase();
    return doc.chunks.filter(c => c.content.toLowerCase().includes(kw));
  }, [doc, filter]);

  // 关键词高亮
  const highlight = (text: string) => {
    if (!filter.trim()) return text;
    const kw = filter.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const parts = text.split(new RegExp(`(${kw})`, "gi"));
    return parts.map((p, i) =>
      p.toLowerCase() === filter.toLowerCase() ? <mark key={i} className="bg-yellow-200 px-0.5 rounded">{p}</mark> : <span key={i}>{p}</span>
    );
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <Link to="/knowledge-base" className="text-sm text-brand-500 hover:underline">&larr; 返回知识库</Link>
      </div>

      {loading ? (
        <DetailSkeleton />
      ) : !doc ? (
        <div className="text-center py-12 text-red-400">文档不存在</div>
      ) : (
        <>
          <h2 className="text-2xl font-bold text-ink mb-2">{doc.filename}</h2>
          <div className="flex items-center gap-3 mb-6">
            <p className="text-sm text-ink-muted">共 {doc.chunks.length} 个切片</p>
            {targetChunk && <span className="text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-600">已定位到切片 #{Number(targetChunk) + 1}</span>}
          </div>

          {/* 页内搜索 */}
          <div className="relative max-w-md mb-6">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
            <input
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="在本文档中搜索关键词..."
              className="w-full pl-9 pr-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            {filter.trim() && (
              <p className="text-xs text-ink-muted mt-1">匹配 {visibleChunks.length} / {doc.chunks.length} 个切片</p>
            )}
          </div>

          <div ref={highlightRef} className="space-y-4">
            {visibleChunks.length === 0 ? (
              <div className="text-center py-10 text-ink-muted bg-white rounded-xl shadow-sm">未找到匹配内容</div>
            ) : (
              visibleChunks.map((chunk) => (
                <div key={chunk.index} id={`chunk-${chunk.index}`} className="bg-white rounded-xl shadow-sm p-4 transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-ink-muted font-mono">切片 #{chunk.index + 1}</span>
                    <button
                      onClick={() => copyChunk(chunk.index, chunk.content)}
                      className="text-xs text-ink-muted hover:text-brand-500 flex items-center gap-1 transition-colors"
                    >
                      {copied === chunk.index ? <><Check className="w-3 h-3" /> 已复制</> : <><Copy className="w-3 h-3" /> 复制</>}
                    </button>
                  </div>
                  <p className="text-sm text-ink leading-relaxed whitespace-pre-wrap">{highlight(chunk.content)}</p>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
