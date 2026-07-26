import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";

interface QARecord {
  index: number;
  question: string;
  answer?: string;
}

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
  const [finished, setFinished] = useState(false);
  const [ending, setEnding] = useState(false);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/interviews/" + id).then(r => r.json()).then(body => {
      if (body.code === 0) {
        const s = body.data;
        setTotal(s.total_questions);
        setCurrentIdx(s.current_question);
        if (s.status === "completed") {
          setFinished(true);
        }
        const qs = (s.questions_asked || []) as QARecord[];
        const answers = (s.answers_given || []) as QARecord[];

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
      }
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
      const r = await fetch("/api/interviews/" + id + "/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: myAnswer }),
      });
      const b = await r.json();
      if (b.code === 0) {
        const data = b.data;
        if (data.is_completed) {
          setFinished(true);
          setCurrentQ("");
        } else {
          setCurrentQ(data.question);
          setCurrentIdx(data.question_index);
          setMessages(prev => [...prev, { role: "ai", text: data.question }]);
        }
      }
    } finally {
      setSending(false);
    }
  };

  const handleEnd = async () => {
    setEnding(true);
    try {
      await fetch("/api/interviews/" + id + "/end", { method: "POST" });
      navigate("/interviews/" + id + "/report");
    } finally {
      setEnding(false);
    }
  };

  if (loading) return <div className="text-center py-12 text-slate-400">加载中...</div>;

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

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, i) => (
          <div key={i} className={"flex " + (msg.role === "user" ? "justify-end" : "justify-start")}>
            <div className={"max-w-[75%] rounded-xl p-4 " + (
              msg.role === "user"
                ? "bg-blue-600 text-white"
                : "bg-white shadow-sm text-slate-800"
            )}>
              <p className={"text-xs mb-1 " + (msg.role === "user" ? "text-blue-200" : "text-slate-400")}>
                {msg.role === "user" ? "你" : "AI 面试官"}
              </p>
              <p className="text-sm">{msg.text}</p>
            </div>
          </div>
        ))}

        <div ref={chatEnd} />
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