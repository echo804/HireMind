import { Link } from "react-router-dom";
import { useTypewriter } from "../hooks/useTypewriter";

/**
 * 欢迎页（极简素蓝白 · 规范 docs/design-system.md §4.1）
 * 独立全屏，不套 Layout；HireMind 动态拼写 → 副语 → CTA 淡入
 */
export default function Welcome() {
  const { displayed, done } = useTypewriter("HireMind");

  return (
    <div className="relative min-h-screen bg-paper flex flex-col items-center justify-center gap-6 px-6 overflow-hidden">
      {/* 极淡蓝光晕 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(700px 380px at 50% 40%, rgb(37 71 235 / 0.05), transparent 70%)",
        }}
      />

      <div className="relative flex flex-col items-center gap-6">
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-brand-700 select-none">
          {displayed}
          {!done && (
            <span className="inline-block w-[3px] h-[1em] bg-brand-700 align-middle ml-1 animate-blink" />
          )}
        </h1>

        <p
          className={`text-sm md:text-base text-brand-500 tracking-wide text-center transition-opacity duration-300 ${
            done ? "opacity-100" : "opacity-0"
          }`}
        >
          让每一次面试，都有备而来
        </p>

        <div
          className={`flex gap-3 transition-opacity duration-300 ${
            done ? "opacity-100" : "opacity-0"
          }`}
        >
          <Link to="/login" className="btn-primary px-8 py-3">
            登录
          </Link>
          <Link to="/register" className="btn-secondary px-8 py-3">
            注册
          </Link>
        </div>
      </div>
    </div>
  );
}
