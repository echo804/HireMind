import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

interface ResumeData {
  id: string; filename: string; file_size: number; file_type: string;
  name: string | null; email: string | null; phone: string | null;
  position: string | null; skills: string[] | null;
  experience: { company: string; title: string; duration: string; description: string }[] | null;
  education: { school: string; degree: string; major: string; year: string }[] | null;
  summary: string | null; score: number | null; status: string; created_at: string;
}

export default function ResumeDetail() {
  const { id } = useParams();
  const [resume, setResume] = useState<ResumeData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/resumes/" + id).then(r => r.json()).then(body => {
      if (body.code === 0) setResume(body.data);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="text-center py-12 text-slate-400">加载中...</div>;
  if (!resume) return <div className="text-center py-12 text-slate-400">简历不存在</div>;

  return (
    <div>
      <Link to="/resumes" className="text-sm text-blue-600 hover:underline">&larr; 返回简历列表</Link>

      <div className="flex items-start justify-between mt-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">{resume.name || resume.filename}</h2>
          <p className="text-slate-500">{resume.position || "未知职位"}</p>
        </div>
        {resume.score && (
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{resume.score}</div>
            <div className="text-xs text-slate-400">综合评分</div>
          </div>
        )}
      </div>

      {resume.summary && (
        <div className="bg-white rounded-xl p-5 shadow-sm mb-4">
          <h3 className="font-semibold text-slate-800 mb-2">专业摘要</h3>
          <p className="text-sm text-slate-600">{resume.summary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-3">联系方式</h3>
          <p className="text-sm text-slate-600">邮箱：{resume.email || "未知"}</p>
          <p className="text-sm text-slate-600">电话：{resume.phone || "未知"}</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-3">技能</h3>
          <div className="flex flex-wrap gap-2">
            {resume.skills?.map((s) => (
              <span key={s} className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">{s}</span>
            )) || <span className="text-sm text-slate-400">无</span>}
          </div>
        </div>
      </div>

      {resume.experience && resume.experience.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm mb-4">
          <h3 className="font-semibold text-slate-800 mb-3">工作经历</h3>
          {resume.experience.map((exp, i) => (
            <div key={i} className="mb-3 pb-3 border-b border-slate-100 last:border-0">
              <p className="font-medium text-slate-800">{exp.title} @ {exp.company}</p>
              <p className="text-xs text-slate-400">{exp.duration}</p>
              <p className="text-sm text-slate-600 mt-1">{exp.description}</p>
            </div>
          ))}
        </div>
      )}

      {resume.education && resume.education.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-3">教育背景</h3>
          {resume.education.map((edu, i) => (
            <div key={i}>
              <p className="font-medium text-slate-800">{edu.school}</p>
              <p className="text-sm text-slate-600">{edu.degree} - {edu.major} ({edu.year})</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
