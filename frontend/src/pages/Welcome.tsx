import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

/**
 * 欢迎页（极简素蓝白 · 规范 docs/design-system.md §4.1 v2）
 * HireMind 字母逐字上浮 + 模糊清晰 + 渐变文字 + 字距舒展 → 副语/CTA 错峰淡入
 * prefers-reduced-motion 时全部直显、无动画
 */
const BRAND = "HireMind";
const TOTAL = 0.3 + BRAND.length * 0.07 + 0.5; // 编排总时长 ≈ 1.4s

const EASE = [0.22, 1, 0.36, 1] as const;

function prefersReducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export default function Welcome() {
  const [reduced] = useState(prefersReducedMotion);
  const [showCursor, setShowCursor] = useState(!reduced);
  const [revealed, setRevealed] = useState(reduced);

  useEffect(() => {
    if (reduced) return;
    const t1 = window.setTimeout(() => setShowCursor(false), (TOTAL + 0.15) * 1000);
    const t2 = window.setTimeout(() => setRevealed(true), (TOTAL + 0.35) * 1000);
    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
    };
  }, [reduced]);

  return (
    <motion.div
      exit={{ opacity: 0, y: -16, filter: "blur(6px)" }}
      transition={{ duration: 0.35, ease: EASE }}
      className="relative min-h-screen bg-paper flex flex-col items-center justify-center gap-10 px-6 overflow-hidden"
    >
      {/* 极淡蓝光晕 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(700px 380px at 50% 40%, rgb(37 71 235 / 0.05), transparent 70%)",
        }}
      />

      <div className="relative flex flex-col items-center gap-8">
        {/* 品牌字：逐字编排 + 渐变 + 字距舒展 */}
        <motion.h1
          initial={{ letterSpacing: "-0.06em" }}
          animate={{ letterSpacing: "-0.02em" }}
          transition={{ duration: 0.9, delay: 0.35, ease: EASE }}
          className="font-display text-5xl md:text-7xl font-bold tracking-tight select-none bg-gradient-to-r from-brand-700 via-brand-500 to-brand-300 bg-clip-text text-transparent"
        >
          <motion.span
            initial="hidden"
            animate="show"
            variants={{
              hidden: {},
              show: { transition: { staggerChildren: 0.07, delayChildren: 0.3 } },
            }}
            className="inline-flex"
          >
            {BRAND.split("").map((ch, i) => (
              <motion.span
                key={i}
                variants={{
                  hidden: { opacity: 0, y: 26, filter: "blur(8px)" },
                  show: {
                    opacity: 1,
                    y: 0,
                    filter: "blur(0px)",
                    transition: { duration: 0.5, ease: EASE },
                  },
                }}
                className="inline-block"
              >
                {ch}
              </motion.span>
            ))}
          </motion.span>
          {showCursor && (
            <span className="inline-block w-[3px] h-[0.9em] bg-brand-500 align-middle ml-1 animate-blink" />
          )}
        </motion.h1>

        {/* 副语 */}
        <motion.p
          initial={reduced ? false : { opacity: 0, y: 12 }}
          animate={reduced || revealed ? { opacity: 1, y: 0 } : { opacity: 0, y: 12 }}
          transition={{ duration: 0.6, ease: EASE }}
          className="text-sm md:text-base text-brand-500 tracking-wide text-center"
        >
          让每一次面试，都有备而来
        </motion.p>

        {/* CTA */}
        <motion.div
          initial={reduced ? false : { opacity: 0, y: 12 }}
          animate={reduced || revealed ? { opacity: 1, y: 0 } : { opacity: 0, y: 12 }}
          transition={{ duration: 0.6, delay: 0.1, ease: EASE }}
          className="flex gap-3"
        >
          <Link to="/login" className="btn-primary px-8 py-3">
            登录
          </Link>
          <Link to="/register" className="btn-secondary px-8 py-3">
            注册
          </Link>
        </motion.div>
      </div>
    </motion.div>
  );
}
