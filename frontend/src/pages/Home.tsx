import { useAuth } from "../contexts/AuthContext";
import { Link } from "react-router-dom";

export default function Home() {
  const { user } = useAuth();

  return (
    <div>
      <div className="text-center mb-16 pt-8">
        <h2 className="text-4xl font-bold text-slate-800 mb-4">
          AI 智能面试官
        </h2>
        <p className="text-lg text-slate-500 max-w-2xl mx-auto">
          基于 AI 的智能面试平台，支持简历解析、模拟面试、实时语音对话
        </p>
        {!user && (
          <Link
            to="/register"
            className="mt-8 inline-block px-8 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            开始使用
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">
            简历解析
          </h3>
          <p className="text-sm text-slate-500">
            AI 自动解析简历，智能评分，去重检测
          </p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">
            模拟面试
          </h3>
          <p className="text-sm text-slate-500">
            文字/语音面试，AI 出题，智能追问
          </p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">
            知识库
          </h3>
          <p className="text-sm text-slate-500">
            文档上传，向量检索，RAG 问答
          </p>
        </div>
      </div>
    </div>
  );
}
