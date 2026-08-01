import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import ConfirmDialog from "../components/ConfirmDialog";

interface QARecord {
  index: number;
  question: string;
  answer?: string;
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
  const [messages, setMessages] = useState<{ role: "ai" | "user"; text: string }[]>([]);
  const [currentQ, setCurrentQ] = useState("");
  const [streamingQ, setStreamingQ] = useState("");
  const [currentIdx, setCurrentIdx] = useState(0);
  const [total, setTotal] = useState(0);
  const [answer, setAnswer] = useState("");
  const [sending, setSending] = useState(false);
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

      const msgs: { role: "ai" | "user"; text: string }[] = [];
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

    try {
      // token 统一从 localStorage "user" 对象读取（与 client.ts 一致）
      let token = "";
      try {
        const saved = localStorage.getItem("user");
        if (saved) token = JSON.parse(saved).token || "";
      } catch {}
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
                break;
              }
              if (chunk.is_completed) {
                setFinished(true);
                break;
              }
              if (chunk.token) {
                setStreamingQ(prev => prev + chunk.token);
              }
              if (chunk.question) {
                // 流式完成：只更新当前问题区域，不重复加入消息列表
                const finalQ = chunk.question;
                setStreamingQ("");
                setCurrentQ(finalQ);
                setCurrentIdx(chunk.question_index);
              }
            } catch {}
          }
        }
      }
    } catch (e: any) {
      setMessages(prev => [...prev, { role: "ai", text: "抱歉，处理你的回答时出现了问题，请重试。" }]);
    } finally {
      setSending(false);
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
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div className={"max-w-[75%] rounded-xl p-4 " + (msg.role === "user" ? userBubble : aiBubble)}>
              <p className={"text-xs mb-1 " + (msg.role === "user" ? userLabel : aiLabel)}>
                {msg.role === "user" ? "你" : "AI 面试官"}
              </p>
              <p className="text-sm leading-relaxed"
                dangerouslySetInnerHTML={{ __html: msg.role === "ai" ? renderMarkdown(msg.text) : msg.text }} />
            </div>
          </div>
        ))}

        <div ref={chatEnd} />

        {currentQ && !finished && !streamingQ && (
          <div className="flex justify-start">
            <div className="max-w-[75%] rounded-xl p-4 bg-white shadow-sm text-ink border border-line">
              <p className="text-xs mb-1 text-ink-muted">AI 面试官</p>
              <p className="text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: renderMarkdown(currentQ) }} />
            </div>
          </div>
        )}

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
        <span className="text-xs text-ink-muted">进度：{currentIdx}/{total}</span>
        <button onClick={() => setEndConfirm(true)} disabled={ending}
          className="text-xs text-red-400 hover:text-red-600">
          {ending ? "处理中..." : "结束面试"}
        </button>
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

      <ConfirmDialog
        open={endConfirm}
        title="结束面试"
        message="确定要结束当前面试吗？已完成的回答将生成评估报告，未答题目不会补问。"
        onConfirm={handleEnd}
        onCancel={() => setEndConfirm(false)}
      />
    </div>
  );
}
