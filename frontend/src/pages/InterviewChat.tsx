import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";

interface QARecord {
  index: number;
  question: string;
  answer?: string;
}

import { ChatSkeleton } from "../components/Skeleton";

export default function InterviewChat() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<{ role: "ai" | "user"; text: string }[]>([]);
  const [currentQ, setCurrentQ] = useState("");
  const [currentIdx, setCurrentIdx] = useState(0);
  const [total, setTotal] = useState(0);
  const [answer, setAnswer] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [finished, setFinished] = useState(false);
  const [ending, setEnding] = useState(false);
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
      let nextQ = "";
      for (const q of qs) {
        msgs.push({ role: "ai", text: q.question });
        const a = answers.find((x: QARecord) => x.index === q.index);
        if (a && a.answer) {
          msgs.push({ role: "user", text: a.answer });
        } else {
          nextQ = q.question;
        }
      }
      setMessages(msgs);
      if (nextQ) setCurrentQ(nextQ);
      setLoading(false);
    }).catch((e) => {
      setError(e.message || "加载面试失败");
      setLoading(false);
    });
  }, [id]);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentQ]);

  const handleSubmit = async () => {
    if (!answer.trim() || sending) return;
    setSending(true);
    const myAnswer = answer.trim();
    setAnswer("");

    setMessages(prev => [...prev, { role: "user", text: myAnswer }]);

    try {
      const data = await api.post<any>("/interviews/" + id + "/answer", { answer: myAnswer });
      if (data.is_completed) {
        setFinished(true);
        setCurrentQ("");
      } else {
        setCurrentQ(data.question);
        setCurrentIdx(data.question_index);
        setMessages(prev => [...prev, { role: "ai", text: data.question }]);
      }
    } catch (e: any) {
      setMessages(prev => [...prev, { role: "ai", text: "抱歉，处理你的回答时出现了问题，请重试。" }]);
    } finally {
      setSending(false);
    }
  };

  const handleEnd = async () => {
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
      <button onClick={() => window.location.reload()} className="text-blue-600 hover:underline">重试</button>
    </div>
  );

  if (finished) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">&#9989;</div>
        <h2 className="text-2xl font-bold text-slate-800 mb-2">面试已完成</h2>
        <p className="text-slate-500 mb-6">共回答 {messages.filter(m => m.role === "user").length} 道题目</p>
        <button onClick={() => navigate("/interviews/" + id + "/report")}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          查看面试报告
        </button>
      </div>
    );
  }

  const aiBubble = "bg-white shadow-sm text-slate-800";
  const userBubble = "bg-blue-600 text-white";
  const aiLabel = "text-slate-400";
  const userLabel = "text-blue-200";

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div className={"max-w-[75%] rounded-xl p-4 " + (msg.role === "user" ? userBubble : aiBubble)}>
              <p className={"text-xs mb-1 " + (msg.role === "user" ? userLabel : aiLabel)}>
                {msg.role === "user" ? "你" : "AI 面试官"}
              </p>
              <p className="text-sm">{msg.text}</p>
            </div>
          </div>
        ))}

        <div ref={chatEnd} />

        {currentQ && !finished && (
          <div className="flex justify-start">
            <div className="max-w-[75%] rounded-xl p-4 bg-white shadow-sm text-slate-800 animate-pulse">
              <p className="text-xs mb-1 text-slate-400">AI 面试官</p>
              <p className="text-sm">{currentQ}</p>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-400">进度：{currentIdx}/{total}</span>
        <button onClick={handleEnd} disabled={ending}
          className="text-xs text-red-400 hover:text-red-600">
          {ending ? "处理中..." : "结束面试"}
        </button>
      </div>

      <div className="flex gap-2">
        <input
          value={answer}
          onChange={e => setAnswer(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder="输入你的回答..."
          className="flex-1 px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        />
        <button
          onClick={handleSubmit}
          disabled={sending || !answer.trim()}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {sending ? "发送中..." : "发送"}
        </button>
      </div>
    </div>
  );
}
