import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { DetailSkeleton } from "../components/Skeleton";

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
        const data = await api.get<any>(`/knowledge/${id}/content`);
        setDoc(data);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  return (
    <div>
      <div className="mb-6">
        <Link to="/knowledge-base" className="text-sm text-brand-500 hover:underline">&larr; 返回知识库</Link>
      </div>

      {loading ? (
        <DetailSkeleton />
      ) : !doc ? (
        <div className="text-center py-12 text-red-400">文档不存在</div>
      ) : (
        <>
          <h2 className="text-2xl font-bold text-ink mb-2">{doc.filename}</h2>
          <p className="text-sm text-ink-muted mb-6">共 {doc.chunks.length} 个切片</p>

          <div className="space-y-4">
            {doc.chunks.map((chunk) => (
              <div key={chunk.index} className="bg-white rounded-xl shadow-sm p-4">
                <span className="text-xs text-ink-muted font-mono mb-2 block">切片 #{chunk.index + 1}</span>
                <p className="text-sm text-ink leading-relaxed whitespace-pre-wrap">{chunk.content}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}