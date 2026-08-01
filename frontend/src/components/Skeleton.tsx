export function CardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl p-5 shadow-sm animate-pulse">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-surface-muted" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-surface-muted rounded w-1/3" />
              <div className="h-3 bg-surface-muted rounded w-2/3" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden animate-pulse">
      <div className="p-4 space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <div className="h-4 bg-surface-muted rounded w-full" />
            <div className="h-4 bg-surface-muted rounded w-1/4 shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function ChatSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className={`flex ${i % 2 === 1 ? "justify-start" : "justify-end"}`}>
          <div className={`rounded-xl p-4 ${i % 2 === 1 ? "bg-white max-w-[75%]" : "bg-brand-100 max-w-[60%]"}`}>
            <div className="h-3 bg-surface-muted rounded w-16 mb-2" />
            <div className="h-3 bg-surface-muted rounded w-48 mb-1" />
            <div className="h-3 bg-surface-muted rounded w-32" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DetailSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-surface-muted rounded w-1/3" />
      <div className="h-4 bg-surface-muted rounded w-1/4" />
      <div className="space-y-3 mt-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl p-4 shadow-sm">
            <div className="h-3 bg-surface-muted rounded w-16 mb-2" />
            <div className="h-4 bg-surface-muted rounded w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
