import { useState, useEffect, useCallback } from "react";
import { api } from "../api/client";
import { TableSkeleton } from "../components/Skeleton";
interface ScheduleEvent {
  id: string;
  candidate_name: string;
  candidate_email: string | null;
  schedule_type: string;
  status: string;
  scheduled_at: string;
  duration_minutes: number;
  notes: string | null;
}

const TYPE_LABELS: Record<string, string> = {
  first: "初面", technical: "技术面", hr: "HR 面",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "待面试", in_progress: "面试中", completed: "已完成", cancelled: "已取消",
};

function getWeekDates(date: Date) {
  const d = new Date(date);
  const day = d.getDay();
  const start = new Date(d);
  start.setDate(d.getDate() - (day === 0 ? 6 : day - 1));
  const dates: Date[] = [];
  for (let i = 0; i < 7; i++) {
    const dd = new Date(start);
    dd.setDate(start.getDate() + i);
    dates.push(dd);
  }
  return dates;
}

function formatDate(d: Date) {
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
}

export default function Schedule() {
  const [events, setEvents] = useState<ScheduleEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [showForm, setShowForm] = useState(false);
  const [editEvent, setEditEvent] = useState<ScheduleEvent | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [form, setForm] = useState({
    candidate_name: "",
    candidate_email: "",
    schedule_type: "technical",
    scheduled_at: "",
    duration_minutes: 60,
    notes: "",
  });

  const weekDates = getWeekDates(currentWeek);
  const weekStart = weekDates[0];
  const weekEnd = weekDates[6];

  const loadEvents = useCallback(async () => {
    try {
      const data = await api.get<any>(`/schedule/range?start=${weekStart.toISOString()}&end=${new Date(weekEnd.getFullYear(), weekEnd.getMonth(), weekEnd.getDate(), 23, 59, 59).toISOString()}`);
      setEvents(data || []);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [weekStart, weekEnd]);

  useEffect(() => { loadEvents(); }, [loadEvents]);

  const getEventsForDate = (d: Date) =>
    events.filter(e => e.scheduled_at.slice(0, 10) === formatDate(d))
      .sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at));

  const openCreate = (date?: string) => {
    setEditEvent(null);
    setForm({ candidate_name: "", candidate_email: "", schedule_type: "technical", scheduled_at: date || "", duration_minutes: 60, notes: "" });
    setShowForm(true);
  };

  const openEdit = (e: ScheduleEvent) => {
    setEditEvent(e);
    setForm({
      candidate_name: e.candidate_name,
      candidate_email: e.candidate_email || "",
      schedule_type: e.schedule_type,
      scheduled_at: e.scheduled_at.slice(0, 16),
      duration_minutes: e.duration_minutes,
      notes: e.notes || "",
    });
    setShowForm(true);
  };

  const handleSave = async () => {
    if (editEvent) {
      await api.put(`/schedule/${editEvent.id}`, form);
    } else {
      await api.post("/schedule", { ...form, scheduled_at: form.scheduled_at + ":00+08:00" });
    }
    setShowForm(false);
    await loadEvents();
  };

  const handleDelete = async (id: string) => {
    await api.delete(`/schedule/${id}`);
    await loadEvents();
  };

  const handleStatusChange = async (id: string, status: string) => {
    await api.put(`/schedule/${id}`, { status });
    await loadEvents();
  };

  const prevWeek = () => setCurrentWeek(new Date(currentWeek.getFullYear(), currentWeek.getMonth(), currentWeek.getDate() - 7));
  const nextWeek = () => setCurrentWeek(new Date(currentWeek.getFullYear(), currentWeek.getMonth(), currentWeek.getDate() + 7));
  const today = new Date();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-ink">面试日程</h2>
        <button onClick={() => openCreate()} className="px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors">
          添加日程
        </button>
      </div>

      {/* Week navigation */}
      <div className="flex items-center justify-between mb-4">
        <button onClick={prevWeek} className="text-sm text-ink-secondary hover:text-ink">&larr; 上一周</button>
        <span className="text-sm font-medium text-ink">
          {weekDates[0].toLocaleDateString("zh-CN")} - {weekDates[6].toLocaleDateString("zh-CN")}
        </span>
        <button onClick={nextWeek} className="text-sm text-ink-secondary hover:text-ink">下一周 &rarr;</button>
      </div>

      {/* Week calendar grid */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden mb-6">
        <div className="grid grid-cols-7 border-b border-line">
          {["一", "二", "三", "四", "五", "六", "日"].map((d, i) => (
            <div key={d} className="p-3 text-center border-r border-line last:border-r-0">
              <p className="text-xs text-ink-muted">{d}</p>
              <p className={formatDate(weekDates[i]) === formatDate(today) ? "text-lg font-semibold mt-1 text-brand-600" : "text-lg font-semibold mt-1 text-ink"}>{weekDates[i].getDate()}</p>
            </div>
          ))}
        </div>

        {loading ? (
          <TableSkeleton rows={4} />
        ) : (
          <div className="grid grid-cols-7 min-h-[300px]">
            {weekDates.map((d, i) => {
              const dayEvents = getEventsForDate(d);
              return (
                <div key={i} className="p-2 border-r border-b border-line last:border-r-0 min-h-[80px]"
                  onClick={() => openCreate(formatDate(d) + "T10:00")}>
                  {dayEvents.map(e => (
                    <div key={e.id} onClick={e => e.stopPropagation()}
                      className="text-xs p-1.5 mb-1 rounded bg-brand-50 text-brand-700 cursor-pointer hover:bg-brand-100 truncate">
                      {e.candidate_name}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Day events list */}
      {!loading && events.length > 0 && (
        <div>
          <h3 className="font-semibold text-ink mb-3">本周安排</h3>
          <div className="grid gap-3">
            {events.sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at)).map(e => (
              <div key={e.id} className="bg-white rounded-xl p-4 shadow-sm flex items-center justify-between">
                <div>
                  <p className="font-medium text-ink">{e.candidate_name}</p>
                  <p className="text-sm text-ink-muted">
                    {new Date(e.scheduled_at).toLocaleString("zh-CN")} &middot; {e.duration_minutes}分钟 &middot; {TYPE_LABELS[e.schedule_type] || e.schedule_type}
                  </p>
                  {e.notes && <p className="text-xs text-ink-muted mt-1">{e.notes}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <select value={e.status} onChange={ev => handleStatusChange(e.id, ev.target.value)}
                    className="text-xs px-2 py-1 rounded border border-line">
                    {Object.entries(STATUS_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                  <button onClick={() => openEdit(e)} className="text-xs text-brand-500 hover:underline">编辑</button>
                  <button onClick={() => setDeleteTarget(e.id)} className="text-xs text-red-400 hover:text-red-600">删除</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowForm(false)}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-96" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-ink mb-4">{editEvent ? "编辑日程" : "添加日程"}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-ink-secondary mb-1">候选人姓名 *</label>
                <input value={form.candidate_name} onChange={e => setForm({ ...form, candidate_name: e.target.value })}
                  className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
              <div>
                <label className="block text-sm text-ink-secondary mb-1">邮箱</label>
                <input value={form.candidate_email} onChange={e => setForm({ ...form, candidate_email: e.target.value })}
                  className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
              <div>
                <label className="block text-sm text-ink-secondary mb-1">面试类型</label>
                <select value={form.schedule_type} onChange={e => setForm({ ...form, schedule_type: e.target.value })}
                  className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                  <option value="first">初面</option>
                  <option value="technical">技术面</option>
                  <option value="hr">HR 面</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-ink-secondary mb-1">面试时间 *</label>
                <input type="datetime-local" value={form.scheduled_at} onChange={e => setForm({ ...form, scheduled_at: e.target.value })}
                  className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
              <div>
                <label className="block text-sm text-ink-secondary mb-1">时长（分钟）</label>
                <input type="number" value={form.duration_minutes} onChange={e => setForm({ ...form, duration_minutes: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
              <div>
                <label className="block text-sm text-ink-secondary mb-1">备注</label>
                <textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} rows={2}
                  className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-ink-secondary bg-surface-muted rounded-lg hover:bg-surface-muted">取消</button>
              <button onClick={handleSave} className="px-4 py-2 text-sm text-white bg-brand-600 rounded-lg hover:bg-brand-700">{editEvent ? "保存" : "创建"}</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {deleteTarget !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h3 className="text-lg font-semibold text-ink mb-2">确认删除</h3>
            <p className="text-sm text-ink-secondary mb-6">确定要删除该日程吗？此操作不可撤销。</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 text-sm text-ink-secondary bg-surface-muted rounded-lg hover:bg-surface-muted transition-colors">
                取消
              </button>
              <button onClick={async () => {
                if (deleteTarget) {
                  await handleDelete(deleteTarget);
                  setDeleteTarget(null);
                }
              }}
                className="px-4 py-2 text-sm text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors">
                确定删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
