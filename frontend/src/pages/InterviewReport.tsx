import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { useToast } from "../contexts/ToastContext";

interface ReportData {
  session_id: string; direction: string; total_questions: number;
  score: number; feedback: string;
  dimensions: Record<string, number>;
  per_question: { index: number; score: number; comment: string }[];
  strengths: string[]; weaknesses: string[]; suggestions: string[];
  created_at: string;
}

interface SessionData {
  answers_given: { index: number; question: string; answer: string }[];
}

const DIRECTION_LABELS: Record<string, string> = {
  frontend: "前端开发", java: "Java 开发",
  python: "Python 开发", algorithm: "算法与数据结构",
  devops: "DevOps / 运维",
};

const DIM_LABELS: Record<string, string> = {
  tech_depth: "技术深度", clarity: "表达清晰",
  logic: "逻辑思维", experience: "实战经验", learning: "学习能力",
};

async function downloadPDF(sessionId: string) {
  const res = await fetch(`/api/interviews/${sessionId}/export-pdf`);
  if (!res.ok) return alert("导出失败");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `interview-report-${sessionId.slice(0, 8)}.pdf`;
  a.click(); URL.revokeObjectURL(url);
}

/** SVG radar chart — pure inline, no dependencies */
function RadarChart({ dims }: { dims: Record<string, number> }) {
  const keys = Object.keys(dims);
  if (keys.length === 0) return null;
  const n = keys.length;
  const cx = 100, cy = 100, r = 75;
  const angle = (2 * Math.PI) / n;
  const points = (level: number) =>
    keys.map((k, i) => {
      const v = (dims[k] / 100) * r * level;
      return `${cx + Math.sin(i * angle - Math.PI / 2) * v},${cy - Math.cos(i * angle - Math.PI / 2) * v}`;
    });

  return (
    <svg viewBox="0 0 200 200" className="w-full max-w-[300px] mx-auto">
      {/* grid rings */}
      {[0.25, 0.5, 0.75].map(lvl => (
        <polygon key={lvl} points={points(lvl).join(" ")} fill="none" stroke="#e2e8f0" strokeWidth="0.5" />
      ))}
      {/* axes */}
      {keys.map((_, i) => {
        const x = cx + Math.sin(i * angle - Math.PI / 2) * r;
        const y = cy - Math.cos(i * angle - Math.PI / 2) * r;
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#e2e8f0" strokeWidth="0.5" />;
      })}
      {/* data polygon */}
      <polygon points={points(1).join(" ")} fill="rgba(59,130,246,0.25)" stroke="#3b82f6" strokeWidth="1.5" />
      {/* data dots */}
      {keys.map((k, i) => {
        const v = (dims[k] / 100) * r;
        const x = cx + Math.sin(i * angle - Math.PI / 2) * v;
        const y = cy - Math.cos(i * angle - Math.PI / 2) * v;
        return <circle key={i} cx={x} cy={y} r="3" fill="#2563eb" />;
      })}
      {/* labels */}
      {keys.map((k, i) => {
        const x = cx + Math.sin(i * angle - Math.PI / 2) * (r + 18);
        const y = cy - Math.cos(i * angle - Math.PI / 2) * (r + 18);
        return (
          <text key={k} x={x} y={y} textAnchor="middle" dominantBaseline="middle"
            className="fill-slate-600" style={{ fontSize: "9px" }}>
            {DIM_LABELS[k] || k}
          </text>
        );
      })}
      {/* center score */}
      <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle"
        className="fill-blue-600 font-bold" style={{ fontSize: "18px" }}>
        {Math.round(keys.reduce((s, k) => s + dims[k], 0) / n)}
      </text>
    </svg>
  );
}

function RingScore({ score }: { score: number }) {
  const color = score >= 80 ? "#16a34a" : score >= 60 ? "#ca8a04" : "#dc2626";
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="relative w-28 h-28">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
        <circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold" style={{ color }}>{score}</span>
        <span className="text-[10px] text-slate-400">总分</span>
      </div>
    </div>
  );
}

export default function InterviewReport() {
  const { id } = useParams();
  const { toast } = useToast();
  const [report, setReport] = useState<ReportData | null>(null);
  const [session, setSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [openQA, setOpenQA] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<any>("/interviews/" + id + "/report"),
      api.get<any>("/interviews/" + id),
    ]).then(([reportData, sessionData]) => {
      setReport(reportData);
      setSession(sessionData);
    }).catch(() => toast("加载面试报告失败", "error")).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <DetailSkeleton />;
  if (!report) return <div className="text-center py-12 text-slate-400">报告不存在</div>;

  const score = report.score;
  const scoreColor = score >= 80 ? "#16a34a" : score >= 60 ? "#ca8a04" : "#dc2626";

  const answers: { index: number; question: string; answer: string; score?: number; comment?: string }[] =
    (session?.answers_given || []).map(a => {
      const pq = (report.per_question || []).find(p => p.index === a.index);
      return { ...a, score: pq?.score, comment: pq?.comment };
    });

  return (
    <div>
      <Link to="/interviews" className="text-sm text-blue-600 hover:underline">&larr; 返回面试列表</Link>

      {/* ─── Banner ─── */}
      <div className="mt-4 rounded-2xl p-8 bg-white shadow-sm">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 mb-1">面试报告</h1>
            <p className="text-slate-400 text-sm">
              {DIRECTION_LABELS[report.direction] || report.direction} &middot; {report.total_questions} 题 &middot;{" "}
              {new Date(report.created_at).toLocaleDateString("zh-CN")}
            </p>
          </div>
          <RingScore score={score} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">

        {/* ─── 左列：雷达图 + 问答回顾 ─── */}
        <div className="space-y-4">
          {/* 雷达图 */}
          {report.dimensions && Object.keys(report.dimensions).length > 0 && (
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <h3 className="font-semibold text-slate-800 mb-3">能力雷达</h3>
              <RadarChart dims={report.dimensions} />
            </div>
          )}

          {/* 综合评价 */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-slate-800 mb-3">综合评价</h3>
            <p className="text-sm text-slate-600 leading-relaxed">{report.feedback}</p>
          </div>

          {/* 问答回顾 */}
          {answers.length > 0 && (
            <div className="bg-white rounded-xl p-5 shadow-sm">
              <h3 className="font-semibold text-slate-800 mb-3">问答回顾</h3>
              <div className="space-y-2">
                {answers.map((a) => (
                  <div key={a.index} className="border border-slate-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => setOpenQA(openQA === a.index ? null : a.index)}
                      className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                    >
                      <span className="text-sm font-medium text-slate-700">
                        第{a.index}题
                        {a.score != null && (
                          <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
                            {a.score}/10
                          </span>
                        )}
                      </span>
                      <span className="text-slate-400 text-xs">{openQA === a.index ? "收起 ▲" : "展开 ▼"}</span>
                    </button>
                    {openQA === a.index && (
                      <div className="px-4 pb-4 space-y-2">
                        <div>
                          <p className="text-xs text-slate-400 mb-1">题目</p>
                          <p className="text-sm text-slate-700">{a.question}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400 mb-1">回答</p>
                          <p className="text-sm text-slate-600">{a.answer}</p>
                        </div>
                        {a.comment && (
                          <div>
                            <p className="text-xs text-slate-400 mb-1">点评</p>
                            <p className="text-sm text-slate-500 italic">{a.comment}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ─── 右列：优势 / 不足 / 建议 ─── */}
        <div className="space-y-4">
          <CardGroup title="优势" items={report.strengths} color="green" icon="✓" />
          <CardGroup title="不足" items={report.weaknesses} color="yellow" icon="!" />
          <CardGroup title="建议" items={report.suggestions} color="blue" icon="→" />
        </div>
      </div>

      {/* ─── 底部操作 ─── */}
      <div className="mt-8 flex justify-center gap-3">
        <Link to="/interviews"
          className="px-5 py-2.5 border border-slate-300 text-slate-600 rounded-xl text-sm hover:bg-slate-50 transition-colors">
          返回列表
        </Link>
        <button onClick={() => downloadPDF(report.session_id)}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors">
          📄 导出 PDF
        </button>
      </div>
    </div>
  );
}

function CardGroup({ title, items, color, icon }: {
  title: string; items: string[]; color: string; icon: string;
}) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm">
      <h3 className={
        color === "green" ? "font-semibold mb-3 text-green-600" :
        color === "yellow" ? "font-semibold mb-3 text-yellow-600" :
        "font-semibold mb-3 text-blue-600"
      }>{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-slate-400">暂无</p>
      ) : (
        <ul className="space-y-2">
          {items.map((s, i) => (
            <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
              <span className={
                color === "green" ? "w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 shrink-0" :
                color === "yellow" ? "w-1.5 h-1.5 rounded-full bg-yellow-500 mt-1.5 shrink-0" :
                "w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"
              } />
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
