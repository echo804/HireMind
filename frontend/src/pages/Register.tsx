import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";

export default function Register() {
  const navigate = useNavigate();
  const { register, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await register({ email, password, nickname });
      navigate("/");
    } catch (err: any) {
      setError(err.message || "注册失败");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-surface-muted to-surface-muted"
    >
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-8">
        <h1 className="text-2xl font-bold text-center text-ink mb-8">
          注册 HireMind
        </h1>
        {error && (
          <div className="mb-4 p-3 text-sm text-red-600 bg-red-50 rounded-lg">{error}</div>
        )}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-ink mb-1">昵称</label>
            <input type="text" value={nickname} onChange={(e) => setNickname(e.target.value)}
              placeholder="请输入昵称" required
              className="w-full px-4 py-2.5 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">邮箱</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="请输入邮箱" required
              className="w-full px-4 py-2.5 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">密码</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder="请设置密码" required
              className="w-full px-4 py-2.5 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
          </div>
          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-brand-600 text-white font-medium rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors">
            {loading ? "注册中..." : "注册"}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-ink-secondary">
          已有账号？{" "}
          <Link to="/login" className="text-brand-600 hover:underline">立即登录</Link>
        </p>
      </div>
    </motion.div>
  );
}
