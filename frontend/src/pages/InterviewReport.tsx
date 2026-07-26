import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

interface ReportData {
  session_id: string; direction: string; total_questions: number;
  score: number; feedback: string;
  strengths: string[]; weaknesses: string[]; suggestions: string[];
  created_at: string;
}

const DIRECTION_LABELS: Record<string, string> = {
  frontend: "前端开发", java: "Java 开发",
  python: "Python 开发", algorithm: "算法与数据结构",
  devops: "DevOps / 运维",
};

export default function InterviewReport() {
  const { id } = useParams();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/interviews/" + id + "/report").then(r => r.json()).then(body => {
      if (body.code === 0) setReport(body.data);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="text-center py-12 text-slate-400">加载中...</div>;
  if (!report) return <div className="text-center py-12 text-slate-400">报告不存在</div>;

  const scoreColor = report.score >= 80 ? "text-green-600" : report.score >= 60 ? "text-yellow-600" : report.score >= 30 ? "text-orange-600" : "text-red-600";
  const scoreLabel = report.score >= 80 ? "优秀" : report.score >= 60 ? "良好" : report.score >= 30 ? "较差" : "未完成";

  return (
    <div>
      <Link to="/interviews" className="text-sm text-blue-600 hover:underline">&larr; 返回面试列表</Link>

      <div className="text-center my-8">
        <div className={"text-5xl font-bold mb-2 " + scoreColor}>{report.score}</div>
        <p className={"text-sm font-medium " + scoreColor}>{scoreLabel}</p>
        <p className="text-slate-500">综合评分</p>
        <p className="text-sm text-slate-400 mt-1">
          {DIRECTION_LABELS[report.direction] || report.direction} &middot;
          共 {report.total_questions} 题 &middot;
          {new Date(report.created_at).toLocaleDateString("zh-CN")}
        </p>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm mb-4">
        <h3 className="font-semibold text-slate-800 mb-3">评价反馈</h3>
        <p className="text-sm text-slate-600 whitespace-pre-line">{report.feedback}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-green-700 mb-3">优势</h3>
          <ul className="space-y-2">
            {report.strengths.map((s, i) => (
              <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>{s}
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-yellow-700 mb-3">不足</h3>
          <ul className="space-y-2">
            {report.weaknesses.map((w, i) => (
              <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                <span className="text-yellow-500 mt-0.5">!</span>{w}
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-blue-700 mb-3">建议</h3>
          <ul className="space-y-2">
            {report.suggestions.map((s, i) => (
              <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">→</span>{s}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
