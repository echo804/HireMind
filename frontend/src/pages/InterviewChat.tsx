import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import ConfirmDialog from "../components/ConfirmDialog";

interface QARecord {
  index: number;
  question: string;
  answer?: string;
}

interface ChatMsg {
  role: "ai" | "user";
  text: string;
  /** AI 对上一题回答的反馈（肯定/纠错） */
  feedback?: string;
}

/** 从问题文本中提取 [来源: xxx] 标注，返回 { 正文, 来源[] } */
function parseSources(text: string): { body: string; sources: string[] } {
  const m = text.match(/\[来源:\s*([^\]]+)\]/);
  if (!m) return { body: text, sources: [] };
  const sources = m[1].split(/[、,，]/).map(s => s.trim()).filter(Boolean);
  return { body: text.replace(m[0], "").trim(), sources };
}

/** 极简 Markdown 渲染：加粗 / 换行 / 代码块 / 行内代码 / 列表 */
function renderMarkdown(text: string) {
  const escape = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  let html = escape(text);
  // 代码块（```...```）
  html = html.replace(/```([\s\S]*?)```/g, (_m, code) =>
    `<pre class="bg-surface-muted rounded-lg p-3 my-2 text-xs overflow-x-auto whitespace-pre-wrap">${code}</pre>`);
  // 行内代码
  html = html.replace(/`([^`]+)`/g, `<code class="bg-surface-muted text-red-500 px-1 rounded text-xs">$1</code>`);
  // 加粗
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  // 无序列表
  html = html.replace(/^[-•]\s+(.+)$/gm, "<li class='ml-4 list-disc'>$1</li>");
  // 换行
  html = html.replace(/\n/g, "<br/>");
  return html;
}

import { ChatSkeleton } from "../components/Skeleton";

export default function InterviewChat() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [currentQ, setCurrentQ] = useState("");
  const [streamingQ, setStreamingQ] = useState("");
  const [currentIdx, setCurrentIdx] = useState(0);
  const [total, setTotal] = useState(0);
  const [lastEval, setLastEval] = useState<number | null>(null);
  const [difficulty, setDifficulty] = useState("normal");
  const [answer, setAnswer] = useState("");
  const [sending, setSending] = useState(false);
  const [skipping, setSkipping] = useState(false);
  const [hinting, setHinting] = useState(false);
  const [hintModal, setHintModal] = useState<string | null>(null);
  const [polishing, setPolishing] = useState(false);
  const [timeLeft, setTimeLeft] = useState(180);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [finished, setFinished] = useState(false);
  const [ending, setEnding] = useState(false);
  const [endConfirm, setEndConfirm] = useState(false);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get<any>("/interviews/" + id).then(data => {
      setTotal(data.total_questions);
      setCurrentIdx(data.current_question);
      if (data.status === "completed") {
        setFinished(true);
      }
      const qs = (data.questions_asked || []) as QARecord[];
      const answers = (data.answers_given || []) as QARecord[];

      const msgs: ChatMsg[] = [];
      for (const q of qs) {
        const a = answers.find((x: QARecord) => x.index === q.index);
        if (a && a.answer) {
          // 已答题目：完整展示问答对
          msgs.push({ role: "ai", text: q.question });
          msgs.push({ role: "user", text: a.answer });
        } else {
          // 当前待回答的问题：只显示在"当前问题"区域，避免重复
          setCurrentQ(q.question);
        }
      }
      setMessages(msgs);
      setLoading(false);
    }).catch((e) => {
      setError(e.message || "加载面试失败");
      setLoading(false);
    });
  }, [id]);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentQ, streamingQ]);

  // 每题计时器：新问题出现时重置 180s，倒计时到 0 提示
  useEffect(() => {
    setTimeLeft(180);
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [currentQ, currentIdx]);

  const handleSubmit = async () => {
    if (!answer.trim() || sending) return;
    setSending(true);
    const myAnswer = answer.trim();
    setAnswer("");

    if (currentQ) {
      // 把当前问题补进消息列表（AI 提问在前、用户回答在后），避免上一题提问丢失
      setMessages(prev => [...prev, { role: "ai", text: currentQ }, { role: "user", text: myAnswer }]);
    } else {
      setMessages(prev => [...prev, { role: "user", text: myAnswer }]);
    }
    setCurrentQ("");
    setStreamingQ("");

    // token 统一从 localStorage "user" 对象读取（与 client.ts 一致）
    let token = "";
    try {
      const saved = localStorage.getItem("user");
      if (saved) token = JSON.parse(saved).token || "";
    } catch {}

    // 带重试的提交：断线/网络抖动时自动重连（最多 2 次），重试前同步服务端状态避免重复提交
    const submitWithRetry = async (attempt: number): Promise<boolean> => {
      try {
        const response = await fetch(`/api/interviews/${id}/answer-stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ answer: myAnswer }),
        });

        if (!response.ok) {
          throw new Error("请求失败");
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("无法读取响应流");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const chunk = JSON.parse(line.slice(6));
                if (chunk.error) {
                  setMessages(prev => [...prev, { role: "ai", text: `错误：${chunk.error}` }]);
                  return true;
                }
                if (chunk.is_completed) {
                  setFinished(true);
                  return true;
                }
                if (chunk.token) {
                  setStreamingQ(prev => prev + chunk.token);
                }
                if (chunk.question) {
                  // 流式完成：先插入对上一回答的反馈，再更新当前问题区域
                  const finalQ = chunk.question;
                  if (chunk.feedback) {
                    setMessages(prev => [...prev, { role: "ai", text: chunk.feedback, feedback: chunk.feedback }]);
                  }
                  setStreamingQ("");
                  setCurrentQ(finalQ);
                  setCurrentIdx(chunk.question_index);
                  if (typeof chunk.evaluation === "number") setLastEval(chunk.evaluation);
                  if (chunk.difficulty) setDifficulty(chunk.difficulty);
                }
              } catch {}
            }
          }
        }
        return true;
      } catch (e) {
        // 流中断：重试前同步服务端状态，避免重复提交同一答案
        if (attempt < 2) {
          try {
            const snap = await api.get<any>("/interviews/" + id);
            const answers = (snap.answers_given || []) as QARecord[];
            const answered = answers.find((x: QARecord) => x.index === currentIdx + 1);
            if (answered) {
              // 服务端已处理该答案：恢复状态，不重发
              const qs = (snap.questions_asked || []) as QARecord[];
              const lastQ = qs.find((x: QARecord) => x.index === currentIdx + 1);
              if (lastQ) {
                if (snap.feedback && lastQ.question) {
                  // 反馈已在首次请求中展示（本地乐观渲染），仅更新当前问题
                }
                setStreamingQ("");
                setCurrentQ(lastQ.question);
                setCurrentIdx(currentIdx + 1);
                setTotal(snap.total_questions);
              }
              if (snap.status === "completed") setFinished(true);
              return true;
            }
          } catch {}
          // 服务端尚未处理：短暂等待后重试
          await new Promise(r => setTimeout(r, 1000));
          return submitWithRetry(attempt + 1);
        }
        setMessages(prev => [...prev, { role: "ai", text: "网络不稳定，回答未送达，请重试。" }]);
        return false;
      }
    };

    try {
      await submitWithRetry(0);
    } finally {
      setSending(false);
    }
  };

  const handleSkip = async () => {
    if (skipping || sending) return;
    setSkipping(true);
    setCurrentQ("");
    setStreamingQ("");
    try {
      let token = "";
      try {
        const saved = localStorage.getItem("user");
        if (saved) token = JSON.parse(saved).token || "";
      } catch {}
      const response = await fetch(`/api/interviews/${id}/skip`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({}),
      });
      if (!response.ok) throw new Error("跳过失败");
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const chunk = JSON.parse(line.slice(6));
            if (chunk.error) { setMessages(prev => [...prev, { role: "ai", text: `错误：${chunk.error}` }]); break; }
            if (chunk.token) setStreamingQ(prev => prev + chunk.token);
            if (chunk.question) {
              setMessages(prev => [...prev, { role: "ai", text: chunk.feedback || "你跳过了上一题。" }]);
              setStreamingQ("");
              setCurrentQ(chunk.question);
              setCurrentIdx(chunk.question_index);
              if (chunk.difficulty) setDifficulty(chunk.difficulty);
            }
          } catch {}
        }
      }
    } catch {
      setMessages(prev => [...prev, { role: "ai", text: "跳过失败，请重试。" }]);
    } finally {
      setSkipping(false);
    }
  };

  const handleHint = async () => {
    if (hinting || !currentQ) return;
    setHinting(true);
    try {
      let token = "";
      try {
        const saved = localStorage.getItem("user");
        if (saved) token = JSON.parse(saved).token || "";
      } catch {}
      const response = await fetch(`/api/interviews/${id}/hint`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({}),
      });
      if (!response.ok) throw new Error("提示失败");
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let hintText = "";
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const chunk = JSON.parse(line.slice(6));
            if (chunk.token) hintText += chunk.token;
            if (chunk.hint && chunk.hint.length > hintText.length) {
              hintText = chunk.hint;
            }
          } catch {}
        }
      }
      // 提示展示在独立弹窗中，不写入对话流
      setHintModal(hintText || "（提示生成失败，请直接回答或跳过）");
    } catch {
      setHintModal("提示生成失败，请直接回答或跳过。");
    } finally {
      setHinting(false);
    }
  };

  const handlePolish = async () => {
    if (polishing || !answer.trim()) return;
    setPolishing(true);
    try {
      let token = "";
      try {
        const saved = localStorage.getItem("user");
        if (saved) token = JSON.parse(saved).token || "";
      } catch {}
      const response = await fetch(`/api/interviews/${id}/polish`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ answer }),
      });
      if (!response.ok) throw new Error("润色失败");
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let polished = "";
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const chunk = JSON.parse(line.slice(6));
            if (chunk.polished) polished = chunk.polished;
          } catch {}
        }
      }
      if (polished) {
        setAnswer(polished);
        setMessages(prev => [...prev, { role: "ai", text: "✨ 已润色你的回答，请检查后发送。" }]);
      } else {
        setMessages(prev => [...prev, { role: "ai", text: "润色失败，请重试。" }]);
      }
    } catch {
      setMessages(prev => [...prev, { role: "ai", text: "润色失败，请重试。" }]);
    } finally {
      setPolishing(false);
    }
  };

  const handleEnd = async () => {
    setEndConfirm(false);
    setEnding(true);
    try {
      await api.post("/interviews/" + id + "/end");
      navigate("/interviews/" + id + "/report");
    } catch (e: any) {
      // still navigate to report even if end request fails
      navigate("/interviews/" + id + "/report");
    } finally {
      setEnding(false);
    }
  };

  if (loading) return <ChatSkeleton />;
  if (error) return (
    <div className="text-center py-12">
      <p className="text-red-500 mb-4">{error}</p>
      <button onClick={() => window.location.reload()} className="text-brand-600 hover:underline">重试</button>
    </div>
  );

  if (finished) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">&#9989;</div>
        <h2 className="text-2xl font-bold text-ink mb-2">面试已完成</h2>
        <p className="text-ink-secondary mb-6">共回答 {messages.filter(m => m.role === "user").length} 道题目</p>
        <button onClick={() => navigate("/interviews/" + id + "/report")}
          className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors">
          查看面试报告
        </button>
      </div>
    );
  }

  const aiBubble = "bg-white shadow-sm text-ink";
  const userBubble = "bg-brand-600 text-white";
  const aiLabel = "text-ink-muted";
  const userLabel = "text-brand-200";

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, i) => {
          const isFeedback = Boolean(msg.feedback);
          // 来源标注解析（仅 AI 问题消息）
          const { body, sources } = isFeedback ? { body: msg.text, sources: [] } : parseSources(msg.text);
          return (
            <div key={i} className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div className={
                "max-w-[75%] rounded-xl p-4 " +
                (msg.role === "user" ? userBubble :
                 isFeedback ? "bg-brand-50 border border-brand-100 shadow-sm text-ink" : aiBubble)
              }>
                <p className={"text-xs mb-1 " + (msg.role === "user" ? userLabel : aiLabel)}>
                  {msg.role === "user" ? "你" : isFeedback ? "💬 AI 面试官反馈" : "AI 面试官"}
                </p>
                <p className="text-sm leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: msg.role === "ai" ? renderMarkdown(body) : msg.text }} />
                {sources.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {sources.map(s => (
                      <span key={s} className="text-[11px] px-1.5 py-0.5 rounded bg-brand-100 text-brand-700">
                        📚 {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        <div ref={chatEnd} />

        {currentQ && !finished && !streamingQ && (() => {
          const { body, sources } = parseSources(currentQ);
          return (
            <div className="flex justify-start">
              <div className="max-w-[75%] rounded-xl p-4 bg-white shadow-sm text-ink border border-line">
                <p className="text-xs mb-1 text-ink-muted">AI 面试官</p>
                <p className="text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: renderMarkdown(body) }} />
                {sources.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {sources.map(s => (
                      <span key={s} className="text-[11px] px-1.5 py-0.5 rounded bg-brand-100 text-brand-700">
                        📚 {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })()}

        {streamingQ && (
          <div className="flex justify-start">
            <div className="max-w-[75%] rounded-xl p-4 bg-white shadow-sm text-ink">
              <p className="text-xs mb-1 text-ink-muted">AI 面试官正在输入...</p>
              <p className="text-sm" dangerouslySetInnerHTML={{ __html: renderMarkdown(streamingQ) }} />
              <span className="inline-block w-1.5 h-4 bg-brand-500 animate-pulse align-middle" />
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="text-xs text-ink-muted">进度：{currentIdx}/{total}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${difficulty === "hard" ? "bg-red-100 text-red-700" : difficulty === "easy" ? "bg-green-100 text-green-700" : "bg-blue-100 text-blue-700"}`}>
            {difficulty === "hard" ? "进阶" : difficulty === "easy" ? "基础" : "标准"}
          </span>
          {lastEval !== null && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">上题得分 {lastEval}/10</span>
          )}
          {timeLeft > 0 && timeLeft < 180 && (
            <span className={`text-xs ${timeLeft <= 30 ? "text-red-500 font-medium" : "text-ink-muted"}`}>
              ⏱ {Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, "0")}
            </span>
          )}
          {timeLeft === 0 && <span className="text-xs text-red-500 font-medium">时间到，请尽快回答或跳过</span>}
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleSkip} disabled={skipping || sending || !currentQ}
            className="text-xs px-3 py-1.5 bg-surface-muted text-ink-secondary rounded-lg hover:bg-line disabled:opacity-50 transition-colors">
            {skipping ? "跳转中..." : "跳过此题"}
          </button>
          <button onClick={() => setEndConfirm(true)} disabled={ending}
            className="text-xs text-red-400 hover:text-red-600">
            {ending ? "处理中..." : "结束面试"}
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-2">
        <button onClick={handleHint} disabled={hinting || !currentQ || sending}
          className="text-xs px-3 py-1.5 bg-amber-50 text-amber-700 border border-amber-200 rounded-lg hover:bg-amber-100 disabled:opacity-50 transition-colors">
          {hinting ? "生成中..." : "💡 请求提示"}
        </button>
        <button onClick={handlePolish} disabled={polishing || !answer.trim() || sending}
          className="text-xs px-3 py-1.5 bg-violet-50 text-violet-700 border border-violet-200 rounded-lg hover:bg-violet-100 disabled:opacity-50 transition-colors">
          {polishing ? "润色中..." : "✨ 润色回答"}
        </button>
        <span className="text-xs text-ink-muted">💡 提示不会计入回答，润色后可检查再发送</span>
      </div>

      <div className="flex items-end gap-2">
        <textarea
          value={answer}
          onChange={e => setAnswer(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          rows={2}
          placeholder="输入你的回答...（Enter 发送，Shift+Enter 换行）"
          className="flex-1 px-4 py-3 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-400 text-sm resize-none"
        />
        <button
          onClick={handleSubmit}
          disabled={sending || !answer.trim()}
          className="px-6 py-3 bg-brand-600 text-white font-medium rounded-xl hover:bg-brand-700 disabled:opacity-50 transition-colors h-[52px]"
        >
          {sending ? "发送中..." : "发送"}
        </button>
      </div>
      <div className="flex justify-end mt-1">
        <span className="text-xs text-ink-muted">已输入 {answer.length} 字</span>
      </div>

      <ConfirmDialog
        open={endConfirm}
        title="结束面试"
        message="确定要结束当前面试吗？已完成的回答将生成评估报告，未答题目不会补问。"
        onConfirm={handleEnd}
        onCancel={() => setEndConfirm(false)}
      />

      {/* 答题提示弹窗 */}
      {hintModal !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setHintModal(null)}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-[480px] max-h-[70vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-ink">💡 答题提示</h3>
              <button onClick={() => setHintModal(null)} className="text-ink-muted hover:text-ink text-xl leading-none">×</button>
            </div>
            <div className="overflow-y-auto text-sm text-ink-secondary whitespace-pre-wrap leading-relaxed">{hintModal}</div>
            <div className="flex justify-end mt-4">
              <button onClick={() => setHintModal(null)}
                className="px-4 py-2 text-sm text-white bg-brand-600 rounded-lg hover:bg-brand-700 transition-colors">
                知道了
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
