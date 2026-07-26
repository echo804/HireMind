import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

interface DocContent {
  id: string;
  filename: string;
  chunks: { index: number; content: string }[];
}

export default function KnowledgeBaseDetail() {
  const { id } = useParams();
  const [doc, setDoc] = useState<DocContent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`/api/knowledge/${id}/content`);
        const b = await r.json();
        if (b.code === 0) setDoc(b.data);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  return (
    <div>
      <div className="mb-6">
        <Link to="/knowledge-base" className="text-sm text-blue-500 hover:underline">&larr; 返回知识库</Link>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : !doc ? (
        <div className="text-center py-12 text-red-400">文档不存在</div>
      ) : (
        <>
          <h2 className="text-2xl font-bold text-slate-800 mb-2">{doc.filename}</h2>
          <p className="text-sm text-slate-400 mb-6">共 {doc.chunks.length} 个切片</p>

          <div className="space-y-4">
            {doc.chunks.map((chunk) => (
              <div key={chunk.index} className="bg-white rounded-xl shadow-sm p-4">
                <span className="text-xs text-slate-400 font-mono mb-2 block">切片 #{chunk.index + 1}</span>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{chunk.content}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}