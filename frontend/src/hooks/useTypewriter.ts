import { useEffect, useState } from "react";

/**
 * 逐字拼写动画 hook（规范 docs/design-system.md §5.1）。
 * - 只播一次，不循环
 * - prefers-reduced-motion 时直接显示完整文本
 */
export function useTypewriter(text: string, speed = 80, startDelay = 400): {
  displayed: string;
  done: boolean;
} {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setDisplayed(text);
      setDone(true);
      return;
    }
    let i = 0;
    let timer: number | undefined;
    const start = window.setTimeout(() => {
      timer = window.setInterval(() => {
        i += 1;
        setDisplayed(text.slice(0, i));
        if (i >= text.length) {
          window.clearInterval(timer);
          setDone(true);
        }
      }, speed);
    }, startDelay);
    return () => {
      window.clearTimeout(start);
      if (timer !== undefined) window.clearInterval(timer);
    };
  }, [text, speed, startDelay]);

  return { displayed, done };
}
