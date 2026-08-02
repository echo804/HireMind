import { useState, useEffect, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useToast } from "../contexts/ToastContext";
import { TableSkeleton } from "../components/Skeleton";

interface ReviewItem {
  session_id: string;
  direction: string;
  index: number;
  question: string;
  answer: string;
  score: number | null;
  comment: string;
  created_at: string | null;
}

const DIRECTION_LABELS: Record<string, string> = {
  frontend: "前端开发", java: "Java 开发", python: "Python 开发", go: "Go 开发",
  rust: "Rust 开发", algorithm: "算法与数据结构", ai_algorithm: "AI 算法工程师",
  llm_engineer: "大模型应用开发", nlp_engineer: "NLP 自然语言处理",
  cv_engineer: "计算机视觉工程师", data_science: "数据科学", devops: "DevOps / SRE",
  backend: "后端开发", fullstack: "全栈开发", product_manager: "产品经理",
};

const scoreColor = (score: number | null) => {
  if (score === null) return "bg-gray-100 text-gray-600";
  if (score >= 8) return "bg-green-100 text-green-700";
  if (score >= 6) return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-700";
};

export default function ReviewNotebook() {
  const { toast } = useToast();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<"list" | "card">("list");
  const [query, setQuery] = useState("");
  const [directionFilter, setDirectionFilter] = useState("all");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [cardIdx, setCardIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await api.get<any>("/interviews/review");
      setItems(data || []);
    } catch {
      toast("加载回顾本失败", "error");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const directions = useMemo(() => {
    const set = new Set(items.map(i => i.direction));
    return Array.from(set);
  }, [items]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter(i => {
      if (directionFilter !== "all" && i.direction !== directionFilter) return false;
      if (q && !i.question.toLowerCase().includes(q) && !i.answer.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [items, query, directionFilter]);

  // 抽认卡模式：切换筛选/搜索时重置索引
  useEffect(() => {
    setCardIdx(0);
    setRevealed(false);
  }, [mode, directionFilter, query]);

  const toggleExpand = (key: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  if (loading) return <TableSkeleton rows={5} />;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-ink">面试回顾本</h2>
          <p className="text-sm text-ink-muted mt-1">复习历史面试中的问题、你的回答与 AI 点评</p>
        </div>
        <div className="flex items-center gap-1 bg-surface-muted rounded-lg p-1">
          <button onClick={() => setMode("list")}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${mode === "list" ? "bg-white shadow-sm text-brand-600 font-medium" : "text-ink-secondary"}`}>
            列表
          </button>
          <button onClick={() => setMode("card")}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${mode === "card" ? "bg-white shadow-sm text-brand-600 font-medium" : "text-ink-secondary"}`}>
            抽认卡
          </button>
        </div>
      </div>

      {/* 搜索 + 方向筛选 */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="搜索问题或回答..."
          className="flex-1 min-w-[200px] px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40"
        />
        <select value={directionFilter} onChange={e => setDirectionFilter(e.target.value)}
          className="px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
          <option value="all">全部方向</option>
          {directions.map(d => (
            <option key={d} value={d}>{DIRECTION_LABELS[d] || d}</option>
          ))}
        </select>
        <span className="text-sm text-ink-muted">{filtered.length} 道题</span>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-ink-muted">
          暂无题目。完成一场面试后，这里会收录面试官的问题供你复习。
        </div>
      ) : mode === "list" ? (
        /* ===== 列表模式：按方向分组 ===== */
        <div className="space-y-6">
          {directions.filter(d => directionFilter === "all" || d === directionFilter).map(d => {
            const groupItems = filtered.filter(i => i.direction === d);
            if (groupItems.length === 0) return null;
            return (
              <div key={d}>
                <h3 className="font-semibold text-ink mb-3 flex items-center gap-2">
                  {DIRECTION_LABELS[d] || d}
                  <span className="text-xs font-normal text-ink-muted">{groupItems.length} 题</span>
                </h3>
                <div className="space-y-2">
                  {groupItems.map((item, i) => {
                    const key = `${item.session_id}-${item.index}`;
                    const open = expanded.has(key);
                    return (
                      <div key={key} className="bg-white rounded-xl p-4 shadow-sm border border-line">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm font-medium text-ink leading-relaxed">
                            <span className="text-ink-muted mr-2">Q{i + 1}.</span>{item.question}
                          </p>
                          {item.score !== null && (
                            <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${scoreColor(item.score)}`}>
                              {item.score}/10
                            </span>
                          )}
                        </div>
                        <button onClick={() => toggleExpand(key)}
                          className="mt-2 text-xs text-brand-600 hover:underline">
                          {open ? "收起回答" : "展开我的回答"}
                        </button>
                        {open && (
                          <div className="mt-3 space-y-2">
                            <div className="bg-surface-muted rounded-lg p-3">
                              <p className="text-xs text-ink-muted mb-1">我的回答</p>
                              <p className="text-sm text-ink-secondary whitespace-pre-wrap leading-relaxed">{item.answer}</p>
                            </div>
                            {item.comment && (
                              <div className="bg-brand-50 rounded-lg p-3">
                                <p className="text-xs text-brand-600 mb-1">AI 点评</p>
                                <p className="text-sm text-ink-secondary leading-relaxed">{item.comment}</p>
                              </div>
                            )}
                          </div>
                        )}
                        <div className="mt-2 flex items-center justify-between">
                          <span className="text-xs text-ink-muted">
                            {item.created_at ? new Date(item.created_at).toLocaleDateString("zh-CN") : ""}
                          </span>
                          <Link to={`/interviews/${item.session_id}/report`}
                            className="text-xs text-brand-600 hover:underline">
                            查看原报告 →
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* ===== 抽认卡模式 ===== */
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-ink-muted">第 {cardIdx + 1} / {filtered.length} 题</span>
            <span className="text-sm text-ink-muted">
              {DIRECTION_LABELS[filtered[cardIdx]?.direction] || filtered[cardIdx]?.direction || ""}
            </span>
          </div>

          <div className="bg-white rounded-2xl shadow-lg border border-line p-8 min-h-[280px] flex flex-col">
            <div className="flex-1">
              <p className="text-xs text-ink-muted mb-3">问题</p>
              <p className="text-lg font-medium text-ink leading-relaxed">{filtered[cardIdx]?.question}</p>
            </div>

            {revealed ? (
              <div className="mt-6 space-y-4 border-t border-line pt-4">
                <div>
                  <p className="text-xs text-ink-muted mb-1">我的回答</p>
                  <p className="text-sm text-ink-secondary whitespace-pre-wrap leading-relaxed">{filtered[cardIdx]?.answer}</p>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-xs text-ink-muted">AI 点评</p>
                    {filtered[cardIdx]?.score !== null && (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${scoreColor(filtered[cardIdx]?.score ?? null)}`}>
                        {filtered[cardIdx]?.score}/10
                      </span>
                    )}
                  </div>
                  {filtered[cardIdx]?.comment ? (
                    <p className="text-sm text-ink-secondary leading-relaxed">{filtered[cardIdx]?.comment}</p>
                  ) : (
                    <p className="text-sm text-ink-muted">（本题暂无点评）</p>
                  )}
                </div>
              </div>
            ) : (
              <button onClick={() => setRevealed(true)}
                className="mt-6 w-full py-3 bg-brand-600 text-white font-medium rounded-xl hover:bg-brand-700 transition-colors">
                显示我的回答
              </button>
            )}
          </div>

          <div className="flex items-center justify-between mt-4">
            <button onClick={() => { setCardIdx(i => Math.max(0, i - 1)); setRevealed(false); }}
              disabled={cardIdx === 0}
              className="px-5 py-2 text-sm bg-surface-muted text-ink-secondary rounded-lg hover:bg-line disabled:opacity-40 transition-colors">
              ← 上一题
            </button>
            <Link to={`/interviews/${filtered[cardIdx]?.session_id}/report`}
              className="text-xs text-brand-600 hover:underline">
              查看原报告 →
            </Link>
            <button onClick={() => { setCardIdx(i => Math.min(filtered.length - 1, i + 1)); setRevealed(false); }}
              disabled={cardIdx === filtered.length - 1}
              className="px-5 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-40 transition-colors">
              下一题 →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
